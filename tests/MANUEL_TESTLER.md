# Manuel Fizik Testleri

Uygulamada elle yapılacak kontroller. Aksi yazılmadıkça: **rüzgar 10 kt, dümen 0°, otomatik trim açık**.
Rüzgar her zaman **Kuzeyden (0°)** eser. Beklenen değerler varsayılan model parametreleriyle hesaplandı.

Otomatik karşılığı: `.venv/Scripts/python -m pytest tests -v`

## A. Ölü açı (no-go)

| # | Ayar | Beklenen |
|---|------|----------|
| A1 | Pruva **0°** (Sert Kanat) | Rozet **NO-GO**, hız 0.00 kt, Fx negatif (≈ −2.7 N). Rota çizgisi **güneye** (geriye) uzanır. |
| A2 | Pruva **20°**, sonra **30°** | Hâlâ **NO-GO**. Sağ panelde "Ölü açı sınırı" kanatta **±36.8°**, bez yelkende **±34.3°**. |
| A3 | Pruva **sınırın 1–2° altı → üstü** (kanat: 35° → 39°) | Rozet NO-GO'dan **ORSA**'ya geçer; hız 0'dan ~1.1 kt'ye sıçrar. |
| A4 | Aynısını **iskele kontrada** yap (kanat: 325° → 321°) | A3 ile aynı davranış (simetri). |
| A5 | Rüzgarı **5 / 10 / 20 kt** yap, ölü açı sınırına bak | Sınır neredeyse sabit kalmalı (±1°). |
| A6 | Pruva **20°**, Sert Kanat, rota haritasına bak | Tekne rüzgardan düşer (20 s sonra pruva ≈ 51°) ve yol almaya başlar. Bu doğru: kanatta lee-helm var. Bez yelkende pruva ≈ 21°'de kalır, tekne yana sürüklenir. |

## B. Yön ve işaretler

| # | Ayar | Beklenen |
|---|------|----------|
| B1 | Pruva **90°** (Doğu, rüzgar iskeleden) | Fy **+** (sancağa / güneye), drift **+0.7°**, hareket yönü φ ≈ **90.7°**. Yelken sancak tarafında (δs +). |
| B2 | Pruva **270°** | B1'in aynası: Fy **−**, drift **−0.7°**, aynı hız (kanat 2.76 kt). |
| B3 | Pruva 90°, dümen **+10°** | Dönüş **+°/s**, "Sancağa ↻ · boca". Rota sağa kıvrılır. |
| B4 | Pruva 90°, dümen **−20°**. Model parametrelerinden "Rota süresi"ni **60 s** yap. | Kartlar (hız, Fx, Fy, drift) **başlangıç anını** (pruva 90°) gösterir. Sağ üst rozet ise rota sonunda tekne ölü açıda **takılı kalıyorsa** kırmızı **"ÖLÜ AÇIDA KALDI · N. s'de takıldı"** olur ve altında "⟲ Ölü açıda kalıyor" uyarısı çıkar. Tekne ölü açıya girip kendiliğinden çıkabiliyorsa rozet değişmez. **Sert kanat:** rozet **APAZ** kalır (tekne çıkıyor). pruva ~14 s'de 28°'ye kadar ölü açıya girer, sonra lee-helm ile geri düşer ve **sınırın hemen dışında (~39.5°) 0.57 kt ile sürünür**. 20 s'deki 36° bir ara değerdir. **Bez yelken:** rozet **"ÖLÜ AÇIDA KALDI · 5. s'de takıldı"** olmalı. Tekne ~10 s'de 7°'ye kadar orsalar, durur, sonra ~19°'de **ölü açıda kalır** (ileri hız ≈ 0, yana 0.6 kt sürüklenme). İki durumda da tekne rüzgarın karşı tarafına geçmez (kontra değiştirmez). |
| B5 | Pruva 90°, dümen **±20°** | Dönüş yarıçapı ≈ **8 m** (yaklaşık 4–5 tekne boyu). |
| B6 | Rota çizgisinin başlangıç yönü | Yeşil Fx okunun ve "Hareket yönü φ"nin gösterdiği yöne uymalı. |

## C. Hız ve trim

| # | Ayar | Beklenen (kanat / bez) |
|---|------|------------------------|
| C1 | Pruva 45 → 60 → 90 → 120 → 180 | Kanat: 1.57 → 2.21 → 2.76 → 2.58 → 2.79 kt. Bez: 2.57 → 3.42 → 4.07 → 3.77 → 3.00 kt. Orsada hız en düşük olmalı. |
| C2 | Pruva 90°, rüzgar 5 → 10 → 20 kt | Hız rüzgarla birlikte artar. Kanatta oran ≈ 0.28 × rüzgar. |
| C3 | Pruva **180°** (tam pupa) | Hız rüzgardan **çok düşük** (10 kt'de < 3 kt). |
| C4 | Otomatik trim **kapalı**, pruva 90°, **yalnız Sert Kanat**, δs = **−45°** (yanlış taraf) | Hız 0, rozet **YOL YOK**. **Bez yelkende** (ıskota) bu test geçerli değil: bumba rüzgaraltına savrulur, δs +45° olur ve hız 4.04 kt çıkar, bu doğru. Bez yelkende 0 kt görmek için "Rijit servo" seç. |
| C5 | Trim kapalı, δs = 20 / 45 / 62 / 90 (kanat) | 1.53 / 2.01 / **2.76** / 0 kt. En iyi değer, otomatik trimle aynı olmalı. |
| C6 | Bez yelken, Iskota (ip), δs = −60 ile +60 | İkisi de ≈ 3.04 kt (ıskota yalnız çeker, bumba rüzgar altına savrulur). Model parametrelerinden "Rijit servo" seçilince −60 → **0 kt** (yelken ters dolar). |

## E. Dümen 0, yelken optimum: tekne hangi yöne gider?

Ayar: **dümen 0°**, **otomatik trim açık** (Optimum), Model parametreleri → **Rota süresi 60 s**.
Pruvayı 45 / 90 / 135 / 180 yapıp şu satırlara bak: **Hareket yönü φ** (o anki gidiş yönü), **Dönüş** (°/s), **60 s sonra pruva**, **Düz rota dümeni**.

| # | Yelken | Pruva | Hareket yönü φ | Dönüş | 60 s sonra pruva | Anlamı |
|---|--------|-------|----------------|-------|------------------|--------|
| E1 | Sert kanat | 45° | 48.8° | +0.70°/s | ≈72° | Pruvaya bakan yöne, biraz rüzgaraltına (drift +3.8°) gider. Yavaşça rüzgardan düşer. |
| E2 | Sert kanat | 90° | 90.7° | +0.13°/s | ≈96° | Neredeyse düz gider. |
| E3 | Sert kanat | 135° | 135.6° | −0.25°/s | ≈121° | Rüzgara doğru yavaşça orsalar. |
| E4 | Sert kanat | — | — | — | — | **Sonuç:** Kanatlı tekne dümen 0'da kendiliğinden, yavaşça (≈5 dakikada) **pruva ≈105°** (TWA ≈105°) civarına yerleşir. Orada dönüş ≈ 0. Uygulamada rota süresi en fazla 60 s olduğu için bunu yalnızca eğilim olarak görürsün: 60→79°, 150→135°. |
| E5 | Bez yelken | 90° | 90.7° | −0.93°/s | **≈24°** | Rüzgara doğru orsalar ve 60 s içinde **ölü açıya girer**. Rozet **"ÖLÜ AÇIDA KALDI · 53. s'de takıldı"** olmalı. Rota süresi 20 s iken tekne henüz ölü açıya girmediği için rozet APAZ kalır. |
| E6 | Bez yelken | 45 / 135° | 48.3 / 134.9° | ≈ −1°/s | 21 / 79° | Hepsi rüzgara döner. Dümen 0'da bez yelkenli tekne düz gidemez. |
| E7 | Bez yelken | 90° | — | — | — | "Düz rota dümeni" **+1.2°** gösterir. Dümeni +1° yapınca dönüş ≈ 0 olmalı ve tekne düz gitmeli. |
| E8 | Bez yelken | **21°** (takılı) | — | — | — | **Ölü açıdan çıkış:** Otomatik trim açıkken dümen ne olursa olsun pruva 22°'yi geçmez. Otomatik trimi **kapat**, δs = **90** (yelkeni tamamen boşalt), dümen 0, rota süresi 60 s. Tekne geri sürüklenir ve **60 s sonra pruva ≈99°** olur. Sonra trimi tekrar aç ve dümeni +1 yap: tekne ≈4 kt ile yol alır. δs = 45 yetmez: pruva ancak 55°'ye gelir, trim açılınca tekne yine ölü açıya döner. |

**Neden farklı?** Kanadın basınç merkezi (CE) yanal direnç merkezinin önünde, bu yüzden tekne rüzgardan düşer (lee helm). Bez yelkenin CE'si bumba yüzünden geride, bu yüzden tekne rüzgara döner (weather helm). Gerçek teknelerde de hafif orsa eğilimi normaldir. Dümenci ya da otopilot bunu küçük bir dümen açısıyla dengeler.

## D. Gerçekçilik sınırları (bilinen model eksikleri)

| # | Ayar | Gözlem | Gerçekte |
|---|------|--------|----------|
| D1 | Bez yelken, pruva 90°, rüzgar **30 kt** | ~12.9 kt, Fr ≈ 1.57, devrilme uyarısı **yok** (HM 94 / RM 98 N·m) | 1.8 m deplasman gövdesi bu hızlara çıkamaz. Dalga direnci (C_R sabit) eksik. Tekne büyük ihtimalle devrilir ya da baş vurur. **~15 kt üstündeki hız sonuçlarına güvenme.** |
| D2 | Ölü açı ±34–37° | İyimser | Salmasız/sertesiz küçük bir katamaranda genelde **45–55°** olur. Gerçek bir denemeyle karşılaştırıp `Gövde yanal eğim` ve `C_R` değerlerini kalibre et. |
| D3 | Drift apazda <1°, orsada ~6–9° | İyimser | Su çekimi 8 cm olan gövdelerde drift daha büyük çıkar. Gerçek testte GPS rotası ile pusula pruvası arasındaki farkı ölç. |

## F. A→B Rota: gözlem araçları

Ayar: sol menüden **A→B Rota** sayfası, varsayılan senaryo (A 0,0 · B 200,0 · başlangıç sapması 30 m), Sert Kanat, 10 kt.

| # | Ne yapılır | Beklenen |
|---|------------|----------|
| F1 | Grafiklerin üstündeki evre şeridine bak | **Yaklaşma** 0–59 s, **Oturma** 59–81 s, **Rotada** 81–189 s. Bir evreye tıklayınca o evrenin başına gider. Evreler grafiklerde gölge, haritada renkli nokta olarak görünür. |
| F2 | Bir grafiğin üstündeki menüden başka parametre seç (ör. **Dönme momentleri**) | Grafik o parametreye geçer, çok serili grafiklerde renk açıklaması görünür. Sayfa yenilense de seçim kalır. |
| F3 | Sağ paneldeki **Özet** sekmesi | Oturma başladı **59.0 s**, Rotaya oturdu **81.0 s**, Aşım **0.07 m**, En büyük dümen **−35°**, Rotada dümen **−0.2° ±0.2**, Yol verimi **%95**. Evre tablosunda dümen ortalaması Yaklaşma −8.2°, Oturma +4.7°, Rotada −0.2° olmalı. |
| F4 | Özet sekmesinden **CSV · Excel (Türkçe)** indirip Excel'de aç | 756 satır, 44 sütun; sütunlar ayrı ve ondalıklar virgüllü görünür. Python/MATLAB için **CSV · standart** kullanılır. |

## G. Kumanda sayfası (`/kumanda`)

Hazırlık: Chrome ya da Edge'de sol menüden **Kumanda ile sür** sayfasını aç. Kumandayı USB/Bluetooth ile bağla ve **bir tuşuna bas**. Varsayılan senaryo, Sert Kanat, 10 kt.

| # | Ne yapılır | Beklenen |
|---|------------|----------|
| G1 | Kumandada bir tuşa bas | Sağ üstte yeşil **🎮 Kumanda bağlı**, panelde kumandanın adı görünür. Sarı "Standart olmayan eşleme" uyarısı çıkarsa tuş numaraları farklı olabilir. |
| G2 | **Start** (PS: Options) | Zaman ilerler, tekne yol alır (başlangıç 2.76 kt). Tekrar Start: duraklar. |
| G3 | Sol çubuğu yarım **sağa** it, sonra bırak | Dümen δr + olur, pruva artar (sancağa döner). Bırakınca dümen 0'a döner. Tam itişte dümen ±35°. |
| G4 | **RB**'ye 2 kez bas, çubuğa dokunma | Dümen trimi +2°, dümen +2°'de kalır. **LB** azaltır. |
| G5 | Sağ çubuğu sola it | "Oto trim: kapalı" olur, yelken açısı değişir. Sert kanatta sağ/sol açıyı döndürür; bez yelkende sağ kaçırır, sol toplar. |
| G6 | **A** (PS: ✕) | Oto trim tekrar açılır, yelken en iyi açıya döner. |
| G7 | **X** (PS: □) | Otopilot devralır: mor ψ* oku çıkar, sapma e azalır. Tekrar X: dümen sana geçer. |
| G8 | **Back** ile baştan al, hemen **X**, sonra **Start** | Tekne, mor noktalı çizginin (aynı senaryoda otopilot) tam üzerinden gider ve B hizasına ~189 s'de varır. Bu, tarayıcı fiziğinin Python ile aynı olduğunun gözle kontrolüdür. |
| G9 | Otopilot kapalı, dümenle rüzgara dön (pruva → 0°) | Göstergeler başlığında kırmızı **ölü açı!** yazar, tekne yavaşlar. Kokpitteki A bölümüyle aynı davranış. |
| G10 | Sürüşten sonra **CSV** düğmeleri | Sürüşün tamamı 0.25 s aralıkla iner; her satırda o an dümen manuel mi otopilot mu yazar. |
| G11 | Klavye: önce haritaya tıkla, ← → dümen, A/D yelken, Boşluk başlat, P otopilot, T oto trim, R baştan, F görünüm, + − yakınlaştır | G2–G7 ile aynı davranış. Shift + ok tam dümen verir. |
| G12 | Sol menüde Bez Yelken seç, Start, dümene dokunma | Tekne rüzgara doğru orsalar (E5 ile aynı). Sol menüdeki bir ayarı değiştirmek sürüşü baştan başlatır. |

Otomatik karşılığı: `test_js_*` testleri fiziği ve otopilotu Chrome'un motorunda (V8) Python ile karşılaştırır. Bunlar için `.venv/Scripts/python -m pip install mini-racer` gerekir; kurulu değilse atlanır. Kumandanın kendisini otomatik test edemiyoruz, onun için G1–G7 elle yapılmalı.
