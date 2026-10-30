"""
Fizik doğrulama testleri — Modül 1 (statik denge + dinamik rota).

Çalıştırma:  .venv/Scripts/python -m pytest tests -v

Konvansiyonlar (app.py): rüzgar KUZEYDEN (0°) eser; pruva 0°=Kuzey, saat yönü +;
gövde ekseni x ileri, y sancak; Fy>0 sancağa; δr>0 → sancağa dönüş (r>0).
"""
import math
import os
import sys
from dataclasses import replace

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app  # noqa: E402

P = app.Params()
KT = app.KT2MS
SAILS = ("wing", "soft")


def eq(heading, tws=10, dr=0, sail="wing", trim="opt", manual=0, p=P):
    return app.solve_equilibrium(heading, tws, dr, trim, manual, sail, p)


def path(heading, tws=10, dr=0, sail="wing", horizon=20, p=P):
    return app.predict_path(heading, tws, dr, "opt", 0, sail, p, horizon)[0]


# ----------------------------------------------------------------------------
# 1) Ölü açı (no-go)
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("sail", SAILS)
def test_head_to_wind_does_not_move(sail):
    """Rüzgara tam pruva (0°) → itiş yok, tekne yol alamaz."""
    e = eq(0, sail=sail)
    assert e["V"] == 0
    assert e["Fx"] < 0          # rüzgar tekneyi geri iter


@pytest.mark.parametrize("sail", SAILS)
def test_nogo_limit_in_realistic_range(sail):
    """Ölü açı sınırı gerçek yelkenliler için tipik 30°–55° aralığında olmalı."""
    lim = app.nogo_limit(10, sail, P)
    assert lim is not None and 30 <= lim <= 55


@pytest.mark.parametrize("sail", SAILS)
def test_nogo_limit_consistent_with_equilibrium(sail):
    """Sınırın 2° altında durur, 2° üstünde yol alır (iskele ve sancak kontra)."""
    lim = app.nogo_limit(10, sail, P)
    for h in (lim - 2, 360 - (lim - 2)):
        assert eq(h, sail=sail)["V"] == 0
    for h in (lim + 2, 360 - (lim + 2)):
        assert eq(h, sail=sail)["V"] > 0


@pytest.mark.parametrize("sail", SAILS)
def test_nogo_limit_independent_of_wind_speed(sail):
    """Kuvvetler rüzgar hızının karesiyle ölçeklendiği için sınır açısı rüzgar hızıyla pek değişmemeli."""
    lims = [app.nogo_limit(t, sail, P) for t in (5, 10, 20)]
    assert max(lims) - min(lims) < 3.0


@pytest.mark.parametrize("sail", SAILS)
def test_in_irons_drifts_backward_downwind(sail):
    """Rüzgara pruva verip bırakılan tekne kuzeye gitmemeli; geri (güneye) sürüklenmeli."""
    pa = path(0, sail=sail)
    assert pa[-1, 1] < -2.0           # net güneye (rüzgar altı) yer değiştirme
    assert pa[-1, 5] < 0              # u < 0: geri gidiş (sternway)


# ----------------------------------------------------------------------------
# 2) Yön / işaret doğruluğu
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("sail", SAILS)
@pytest.mark.parametrize("h", (45, 60, 90, 120, 150))
def test_port_starboard_mirror_symmetry(sail, h):
    """θ ve 360−θ aynalı olmalı: hız aynı, yanal kuvvet/drift ters işaretli."""
    a, b = eq(h, sail=sail), eq(360 - h, sail=sail)
    assert a["V"] == pytest.approx(b["V"], rel=1e-3)
    assert a["Fy"] == pytest.approx(-b["Fy"], rel=1e-3, abs=1e-3)
    assert a["lam"] == pytest.approx(-b["lam"], rel=1e-3, abs=1e-3)


@pytest.mark.parametrize("sail", SAILS)
def test_leeway_is_downwind(sail):
    """Rüzgar iskeleden (pruva 90°) → yanal kuvvet ve drift sancağa (rüzgar altına)."""
    e = eq(90, sail=sail)
    assert e["Fy"] > 0 and e["lam"] > 0
    assert e["course"] > 90


@pytest.mark.parametrize("h", (60, 90, 135))
def test_path_follows_predicted_course(h):
    """Dinamik rota başlangıç yönü, statik dengenin hareket yönüyle (pruva + drift) uyumlu olmalı."""
    e = eq(h)
    pa = path(h, horizon=5)
    bearing = math.degrees(math.atan2(pa[-1, 0], pa[-1, 1])) % 360
    assert abs(app.wrap180(bearing - e["course"])) < 2.0


@pytest.mark.parametrize("sail", SAILS)
def test_rudder_sign(sail):
    """+δr sancağa (pruva artar), −δr iskeleye döndürür."""
    assert eq(90, dr=+10, sail=sail)["r"] > 0.5
    assert eq(90, dr=-10, sail=sail)["r"] < -0.5
    assert app.wrap180(path(90, dr=+10, sail=sail, horizon=10)[-1, 4] - 90) > 20


def test_turn_radius_plausible():
    """20° dümende dönüş yarıçapı birkaç tekne boyu olmalı (1.8 m tekne → ~3–15 m)."""
    r = eq(90, dr=20)["radius"]
    assert 3 < r < 15


@pytest.mark.parametrize("sail", SAILS)
def test_luffing_into_wind_does_not_tack(sail):
    """Rüzgara doğru tam dümen: tekne rüzgarı geçmemeli (kontra değiştirmemeli) ve
    ölü açı sınırına yakın yerde çok yavaşlamalı (kanat: sınırın hemen dışı, bez: ölü açının içi)."""
    pa = path(90, dr=-20, sail=sail, horizon=60)
    assert (pa[:, 4] > 0).all() and (pa[:, 4] < 91).all()
    lim = app.nogo_limit(10, sail, P)
    assert pa[-1, 4] < lim + 5
    assert pa[-1, 5] < 0.35            # ileri hız (u) çok düşük


# ----------------------------------------------------------------------------
# 3) Hız ve kuvvet büyüklükleri
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("sail", SAILS)
def test_speed_below_true_wind(sail):
    """Bu modelde (folyosuz küçük katamaran) hız her seyir açısında gerçek rüzgarın altında kalmalı."""
    for h in range(40, 181, 10):
        assert eq(h, sail=sail)["V"] < 10 * KT


@pytest.mark.parametrize("sail", SAILS)
def test_dead_downwind_slower_than_wind(sail):
    """Tam pupada tekne rüzgardan hızlı gidemez (görünür rüzgar sıfıra iner)."""
    for t in (5, 10, 20):
        assert eq(180, tws=t, sail=sail)["V"] < 0.6 * t * KT


@pytest.mark.parametrize("sail", SAILS)
def test_speed_increases_with_wind(sail):
    vs = [eq(90, tws=t, sail=sail)["V"] for t in (4, 8, 12, 16)]
    assert all(b > a for a, b in zip(vs, vs[1:]))


@pytest.mark.parametrize("sail", SAILS)
def test_close_hauled_slower_than_beam_reach(sail):
    lim = app.nogo_limit(10, sail, P)
    assert eq(lim + 3, sail=sail)["V"] < eq(90, sail=sail)["V"]


@pytest.mark.parametrize("sail", SAILS)
def test_leeway_larger_close_hauled(sail):
    """Orsada drift, apazdan büyük olmalı; apazda birkaç dereceyi geçmemeli."""
    lim = app.nogo_limit(10, sail, P)
    assert eq(lim + 3, sail=sail)["lam"] > eq(90, sail=sail)["lam"]
    assert 0 < eq(90, sail=sail)["lam"] < 5


@pytest.mark.parametrize("sail", SAILS)
def test_optimum_trim_beats_manual(sail):
    """Otomatik (optimum) trim, elle verilen her açıdan en az onun kadar hızlı olmalı."""
    v_opt = eq(90, sail=sail)["V"]
    for m in range(-90, 91, 15):
        assert eq(90, sail=sail, trim=False, manual=m)["V"] <= v_opt + 1e-6


def test_wing_wrong_side_trim_gives_no_drive():
    """Kanat yanlış tarafa (rüzgarüstü) trim edilirse yol alınmaz."""
    assert eq(90, sail="wing", trim=False, manual=-45)["V"] == 0


# ----------------------------------------------------------------------------
# 4) Sağ üst rozet: rota ölü açıda TAKILIYOR mu? (nogo_trap)
# ----------------------------------------------------------------------------
def trap(sail, h, dr, horizon, trim="opt", manual=0):
    pa = app.predict_path(h, 10, dr, trim, manual, sail, P, horizon)[0]
    return app.nogo_trap(pa, 10, dr, trim, manual, sail, P, app.nogo_limit(10, sail, P))


def test_trap_soft_luffing_into_irons():
    """Bez yelken, 90°'den −20° dümen: ~5. s'de ölü açıya girer ve çıkamaz → takıldı."""
    t = trap("soft", 90, -20, 20)
    assert t is not None and 3 < t < 8


@pytest.mark.parametrize("horizon", (10, 20, 60))
def test_trap_wing_escapes_is_not_flagged(horizon):
    """Kanat aynı manevrada ölü açıya girer ama lee helm ile kendiliğinden çıkar → işaretlenmez."""
    assert trap("wing", 90, -20, horizon) is None


def test_trap_follows_path_horizon():
    """Bez yelken, dümen 0: 20 s'lik rota henüz ölü açıya girmiyor (işaret yok); 60 s'lik rota giriyor ve takılıyor."""
    assert trap("soft", 90, 0, 20) is None
    assert trap("soft", 90, 0, 60) is not None


def test_trap_eased_sail_escape_not_flagged():
    """Yelken tamamen boşaltılınca (δs = 90) bez yelkenli tekne ölü açıdan çıkar → işaretlenmez."""
    assert trap("soft", 21, 0, 60, trim=False, manual=90) is None


def test_trap_normal_sailing_not_flagged():
    assert trap("wing", 90, 0, 20) is None
    assert trap("soft", 90, 0, 10) is None


def _badge(at):
    return next(m.value for m in at.markdown if '<div class="ck-badge"' in m.value)


def test_ui_badge_shows_trap():
    """Arayüz: bez yelken, pruva 90°, dümen −20° → sağ üst rozet ÖLÜ AÇIDA KALDI; kanatta APAZ kalır."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(os.path.dirname(app.__file__), "app.py"), default_timeout=180).run()
    at.slider[1].set_value(-20).run()
    assert "APAZ" in _badge(at)                     # kanat: girip çıkıyor → başlangıç durumu
    at.button[1].click().run()                      # Bez Yelken
    b = _badge(at)
    assert "ÖLÜ AÇIDA KALDI" in b and "takıldı" in b
    assert not at.exception


def test_ui_number_box_and_slider_stay_in_sync():
    """Arayüz: kutuya yazılan değer kaydırıcıya ve hesaba geçer; kaydırıcı da kutuyu günceller."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(os.path.dirname(app.__file__), "app.py"), default_timeout=180).run()
    at.number_input(key="heading__n").set_value(45).run()
    assert at.slider(key="heading__s").value == 45
    assert "ORSA" in _badge(at)
    at.slider(key="tws__s").set_value(15).run()
    assert at.number_input(key="tws__n").value == 15
    assert not at.exception


# ----------------------------------------------------------------------------
# 5) A→B rota otopilotu (fizik aynı, yalnız dümen otopilottan)
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("sail,dr", [("wing", 0), ("soft", -20), ("wing", 15)])
def test_route_eom_identical_to_predict_path(sail, dr):
    """Otopilotun kullandığı hareket denklemleri predict_path ile BİREBİR aynı: sabit dümenle aynı RK4 → aynı rota."""
    h, T, dt = 90.0, 10.0, 0.025
    ref = app.predict_path(h, 10, dr, "opt", 0, sail, P, T)[0]
    e = app.solve_equilibrium(h, 10, dr, "opt", 0, sail, P)
    lam = math.radians(e["lam"])
    st = np.array([0.0, 0.0, h, e["V"] * math.cos(lam), e["V"] * math.sin(lam), math.radians(e["r"])])
    f = lambda s: app._route_deriv(s, math.radians(dr), 10, "opt", 0, sail, P)[0]
    rows = []
    for k in range(1, int(round(T / dt)) + 1):
        k1 = f(st); k2 = f(st + 0.5 * dt * k1); k3 = f(st + 0.5 * dt * k2); k4 = f(st + dt * k3)
        st = st + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        if k % 10 == 0:
            rows.append((st[0], st[1], st[2] % 360.0))
    assert np.allclose(np.array(rows), ref[1:, [0, 1, 4]], atol=1e-9)


def route(sail="wing", B=(200, 0), e0=30, he=0, **ap):
    return app.simulate_route((0, 0), B, e0, he, 10, "opt", 0, sail, P, replace(app.Autopilot(), **ap))


@pytest.mark.parametrize("sail", SAILS)
@pytest.mark.parametrize("e0", (30, -30))
def test_route_converges_onto_line_and_reaches_B(sail, e0):
    """A'nın 30 m dışından başlayan tekne rotaya oturur (|e| < 0.5 m, aşım < 1 m) ve B'ye ulaşır."""
    r = route(sail, e0=e0)
    assert r["status"] == "reached"
    assert abs(r["e"][-1]) < 0.5
    overshoot = -r["e"].min() if e0 > 0 else r["e"].max()
    assert overshoot < 1.0


def test_route_cog_follows_track_with_leeway_feedforward():
    """İleri besleme açıkken rotaya oturan teknenin GİDİŞ yönü (COG) rota açısına eşit; pruva ise yan kayma kadar farklı."""
    r = route("soft", B=(150, -87))
    late = r["t"] > r["t_end"] - 20
    assert abs(app.wrap180(np.mean(r["cog"][late]) - r["chi"])) < 1.0
    assert abs(app.wrap180(np.mean(r["h"][late]) - r["chi"]) + np.mean(r["lam"][late])) < 1.0


def test_route_rudder_limits_respected():
    r = route("wing", e0=60, he=60, rud_max=25, rud_rate=40)
    assert np.abs(r["dr"]).max() <= 25 + 1e-9
    assert np.abs(np.diff(r["dr"])).max() <= 40 * 0.25 + 1e-6


def test_route_in_nogo_is_reported():
    """Rüzgara karşı (ölü açıdaki) rota: doğrudan gidilemez, durum 'nogo'."""
    r = route("wing", B=(40, 200))
    assert r["track_nogo"] and r["status"] == "nogo"


def test_ui_route_mode_renders():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(os.path.dirname(app.__file__), "app.py"), default_timeout=300).run()
    at.radio(key="mode").set_value("A→B Rota").run()
    assert not at.exception
    page = " ".join(m.value for m in at.markdown)
    assert "Varış süresi" in page and "kaskad PID" in page
    assert "Rotaya oturdu" in page and "Yaklaşma" in page and "Rotada" in page   # özet ve evre tablosu
    at.radio(key="mode").set_value("Kokpit").run()       # kokpite geri dönüş bozulmamalı
    assert not at.exception and "APAZ" in _badge(at)


@pytest.mark.parametrize("sail", SAILS)
def test_route_phases_are_ordered_and_consistent(sail):
    """Evreler sırayla gelir; 'Rotada' evresinde |e| hep < 1 m, 'Yaklaşma'da dış döngü doymuştur."""
    r = route(sail)
    ap = app.Autopilot()
    ph = app.route_phases(r, ap)
    assert 0 < ph["t_turn"] < ph["t_settle"] < r["t_end"]
    assert np.all(np.diff(ph["phase"]) >= 0)                       # 0 → 1 → 2, geri dönüş yok
    assert np.all(np.abs(r["e"][ph["phase"] == 2]) < app.SETTLE_BAND)
    assert np.all(np.abs(r["dpsi"][ph["phase"] == 0]) >= ap.dpsi_max - 1e-6)
    assert [x["name"] for x in ph["rows"]] == list(app.PHASES)
    assert abs(sum(x["dur"] for x in ph["rows"]) - r["t"][-1]) < 1e-9
    assert abs(ph["dr_hold"]) < 2.0 and ph["dr_hold_std"] < 1.0    # rotada küçük, sabit dümen
    assert 0.8 < ph["eff"] <= 1.0


def _goto_page(at, *urls):
    """st.navigation sayfasına geçer (AppTest.switch_page yalnız dosya sayfalarını destekliyor)."""
    at._page_hash = next(h for h, i in at._registered_pages.items() if i.get("url_pathname") in urls)
    return at.run()


def test_ui_drive_is_a_separate_page():
    """Kumanda ayrı sayfadır: simülasyon sayfasının mod seçiminde yoktur, kendi sayfasında mod seçimi yoktur."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(os.path.dirname(app.__file__), "app.py"), default_timeout=300).run()
    assert not at.exception and list(at.radio(key="mode").options) == ["Kokpit", "A→B Rota"]
    assert "Kumanda ile sür" not in " ".join(m.value for m in at.markdown)
    _goto_page(at, app.DRIVE_URL)
    assert not at.exception
    assert "Kumanda ile sür" in " ".join(m.value for m in at.markdown)
    assert not [r for r in at.radio if r.key == "mode"]


def test_ui_settings_survive_page_change():
    """Senaryo ve sol menü ayarları sayfa değişince korunur (A→B ile Kumanda aynı senaryoyu kullanır)."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(os.path.dirname(app.__file__), "app.py"), default_timeout=300).run()
    at.radio(key="mode").set_value("A→B Rota").run()
    at.number_input(key="rt_e0__w").set_value(20.0).run()
    at.number_input(key="tws__n").set_value(12).run()
    _goto_page(at, app.DRIVE_URL)
    assert not at.exception
    assert at.number_input(key="rt_e0__w").value == 20.0 and at.number_input(key="tws__n").value == 12
    _goto_page(at, "", "simulasyon")                      # geri dönüş: mod seçimi de korunur
    assert not at.exception and at.radio(key="mode").value == "A→B Rota"
    assert at.number_input(key="rt_e0__w").value == 20.0


def test_drive_html_is_complete():
    """Kumanda sayfasının HTML'i: fizik kodu gömülü, yer tutucu kalmamış, veri JSON'u doğru."""
    import json
    import re
    ap, rs = app.Autopilot(), app.route_start((0, 0), (200, 0), 30, 0, 10, "opt", 45, "soft", P)
    html = app._drive_html(app.route_js(rs), app.sim_env(10, "opt", 45, "soft", P), ap, None, 30, 10, "soft", P)
    assert "__DATA__" not in html and "/*__SIM__*/" not in html and "const SIM = (() =>" in html
    data = json.loads(re.search(r"const D = (\{.*\});\n", html).group(1))
    assert data["env"]["sail"] == "soft" and data["rt"]["L"] == 200.0 and data["ap"]["rud_max"] == ap.rud_max
    assert data["env"]["p"]["m22"] == P.m22                     # türetilmişler Python'dan, bit düzeyinde aynı


def test_route_phases_start_on_line_has_no_approach():
    """Rotanın 2 m yanında başlayan teknede yaklaşma evresi yoktur."""
    r = route(e0=2)
    ph = app.route_phases(r, app.Autopilot())
    assert ph["t_turn"] == 0.0 and [x["name"] for x in ph["rows"]] == ["Oturma", "Rotada"]


def test_route_csv_has_all_columns_both_formats():
    import io
    import pandas as pd
    r = route()
    ph = app.route_phases(r, app.Autopilot())
    std = pd.read_csv(io.BytesIO(app.route_csv(r, ph)), encoding="utf-8-sig")
    tr = pd.read_csv(io.BytesIO(app.route_csv(r, ph, excel_tr=True)), encoding="utf-8-sig", sep=";", decimal=",")
    assert list(std.columns) == [c for _, c in app.ROUTE_CSV] == list(tr.columns)
    assert len(std) == len(tr) == len(r["t"])
    assert np.allclose(std["Sapma e (m)"], r["e"], atol=1e-4)
    assert np.allclose(tr["Dümen açısı δr (°)"], r["dr"], atol=1e-4)
    assert set(std["Evre"]) == set(app.PHASES)


# ----------------------------------------------------------------------------
# 6) Gerçekçilik sınırları — bilinen model eksikleri (xfail = şu an BAŞARISIZ, rapor için)
# ----------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="C_R sabit: dalga direnci tümseği yok → yüksek rüzgarda hız gövde "
                                        "hızının çok üstüne çıkıyor (bez yelken 30 kt'de Fr≈1.6).")
@pytest.mark.parametrize("sail", SAILS)
def test_hull_speed_limit(sail):
    """1.8 m deplasman gövdesi: yarı-kayış olmadan Froude sayısı ~0.7'yi pek aşamaz."""
    assert eq(90, tws=30, sail=sail)["Fr"] < 0.7


def test_rudder_zero_wing_settles_on_beam_reach():
    """Dümen 0, optimum trim: kanat (lee helm) farklı pruvalardan başlayıp yavaşça (~5 dk) TWA ~105°'ye yerleşmeli."""
    for h in (60, 90, 150):
        assert 100 < path(h, horizon=300)[-1, 4] < 112


def test_rudder_zero_soft_rounds_up_into_irons():
    """Dümen 0, optimum trim: bez yelken (weather helm) rüzgara döner ve ölü açıda kalır.
    Düz rota için gereken dümen pozitif (boca yönü) olmalı."""
    lim = app.nogo_limit(10, "soft", P)
    assert path(90, sail="soft", horizon=60)[-1, 4] < lim
    assert eq(90, sail="soft")["d_bal"] > 0
    assert abs(eq(90, sail="soft", dr=eq(90, sail="soft")["d_bal"])["r"]) < 0.05


def test_wing_falls_off_out_of_irons():
    """Kanat CE'si CLR'nin önünde (lee helm): ölü açıda bırakılan tekne rüzgardan düşüp yol almalı.
    Not: üstteki NO-GO rozeti sabit pruva içindir; rota çizgisi teknenin serbest davranışını gösterir."""
    assert eq(20)["V"] == 0
    pa = path(20)
    assert pa[-1, 4] > app.nogo_limit(10, "wing", P)
    assert pa[-1, 5] > 0


# ----------------------------------------------------------------------------
# 7) Tarayıcı fiziği (sim_physics.js, kumandalı sürüş) — Python ile AYNI sonuç
#    JS, Chrome'un motoru V8'de (mini-racer) çalıştırılır.
# ----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def js():
    mr = pytest.importorskip("py_mini_racer")
    ctx = mr.MiniRacer()
    with open(os.path.join(os.path.dirname(app.__file__), "sim_physics.js"), encoding="utf-8") as fh:
        ctx.eval(fh.read())
    return ctx


def _jscall(js, expr, **kw):
    import json
    return js.eval("(() => { " + "".join(f"const {k} = {json.dumps(v)};" for k, v in kw.items()) +
                   f" return JSON.stringify({expr}); }})()")


BF_KEYS = ("X", "Y", "N", "Fx", "Fy", "N_s", "N_h", "N_r", "N_munk", "Y_h", "Y_r", "X_r", "R", "beta", "delta_s")


@pytest.mark.parametrize("sail,trim,rigid", [("wing", "opt", False), ("wing", True, False), ("wing", False, False),
                                             ("soft", "opt", False), ("soft", False, False), ("soft", False, True)])
def test_js_body_forces_identical(js, sail, trim, rigid):
    """Rastgele durumlarda (ileri, geri, yana, dönerken) tüm kuvvetler ve momentler Python ile aynı."""
    import json
    p = replace(P, boom_rigid=rigid)
    rng = np.random.default_rng(1)
    worst = 0.0
    for _ in range(150):
        u, v, r = rng.uniform(-1.5, 3), rng.uniform(-1.5, 1.5), rng.uniform(-0.6, 0.6)
        h, dr, tws, man = rng.uniform(0, 360), rng.uniform(-35, 35), rng.choice((3, 10, 20)), rng.uniform(-90, 90)
        env = app.sim_env(tws, trim, man, sail, p)
        b = app.body_forces(u, v, r, h, tws, math.radians(dr), trim, man, sail, p)
        j = json.loads(_jscall(js, "SIM.bodyForces(u, v, r, h, dr * SIM.D2R, env)", u=u, v=v, r=r, h=h, dr=dr, env=env))
        for k in BF_KEYS:
            worst = max(worst, abs(j[k] - b[k]) / (1.0 + abs(b[k])))
    assert worst < 1e-12


@pytest.mark.parametrize("sail,dr", [("wing", 0), ("soft", -20), ("wing", 15)])
def test_js_fixed_rudder_path_identical(js, sail, dr):
    """Sabit dümenle 60 s: JS RK4 yolu predict_path ile aynı."""
    import json
    env = app.sim_env(10, "opt", 0, sail, P)
    pa, _ = app.predict_path(90, 10, dr, "opt", 0, sail, P, 60)
    eq0 = app.solve_equilibrium(90, 10, dr, "opt", 0, sail, P)
    lam = math.radians(eq0["lam"]) if eq0["V"] > 0 else 0.0
    st0 = [0.0, 0.0, 90.0, eq0["V"] * math.cos(lam), eq0["V"] * math.sin(lam),
           math.radians(eq0["r"]) if eq0["V"] > 0 else 0.0]
    out = json.loads(_jscall(js, """(() => { let st = st0.slice(); const o = [];
        for (let k = 0; k <= 2400; k++) { const [k1] = SIM.deriv(st, dr * SIM.D2R, env);
          if (k % 10 === 0) o.push([st[0], st[1], SIM.pymod(st[2], 360)]); st = SIM.rk4(st, dr * SIM.D2R, env, 0.025, k1); }
        return o; })()""", st0=st0, dr=dr, env=env))
    out = np.array(out)
    assert np.allclose(out[:, 0], pa[:, 0], atol=1e-8) and np.allclose(out[:, 1], pa[:, 1], atol=1e-8)
    assert np.allclose(out[:, 2], pa[:, 4], atol=1e-8)


@pytest.mark.parametrize("sail,e0,he", [("wing", 30, 0), ("soft", -30, 0), ("wing", 10, 60), ("soft", 20, -40)])
def test_js_autopilot_route_identical(js, sail, e0, he):
    """JS kaskad PID + fizik, 90 s boyunca simulate_route ile aynı yolu ve dümeni verir."""
    import json
    A, B, ap = (0, 0), (3000, 0), app.Autopilot()
    rs = app.route_start(A, B, e0, he, 10, "opt", 0, sail, P)
    r = app.simulate_route(A, B, e0, he, 10, "opt", 0, sail, P, ap, t_max=90)
    env, rt = app.sim_env(10, "opt", 0, sail, P), app.route_js(rs)
    apd = {k: getattr(ap, k) for k in ap.__dataclass_fields__}
    j = json.loads(_jscall(js, "SIM.simulateRoute(rt.st0, rt, ap, env, 90)", rt=rt, ap=apd, env=env))
    for k in ("x", "y", "h", "dr", "e"):
        assert np.allclose(j[k], r[k], atol=1e-7), k
