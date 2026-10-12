
# Hakem Değerlendirmeleri ve Madde Madde Yanıtlar


<b>Dinamik Gaz Türbininde PI ve Bozucu Gözlemciler - Türkçe rapor V2</b>


Üç rol açısından eleştirel inceleme | 13 Eylül 2026


Bu çalışma, kullanıcının istediği üç bakış açısıyla yürütülmüş yapay zekâ destekli bir teknik incelemedir; bağımsız insan hakemliği veya dergi kabulü değildir. Endüstri mühendisi rolü ayrı bir ajan tarafından tamamlandı. Kontrol teorisi ve araştırma asistanı rollerindeki paralel işler kullanım sınırında kesildi; bu iki perspektif ana oturumda kaynak, kod ve veri denetimiyle tamamlandı.



## Genel değerlendirme


Ana RMSE, tepe ve ±1 rpm toparlanma tablolarında hesap hatası saptanmadı. Düzeltmelerin odak noktası, sonuçların genellenme sınırı ve kanıt kapsamıdır. En önemli ek bulgu, toparlanma sıralamasının ±0.5/1/2 rpm bandına duyarlı olmasıdır. Nominal terslenebilirlik gösterildi; eşit kutup parametresinin eşit bant olmadığı türetildi; fiziksel eyleyici ve gömülü yeterlilik iddiaları sınırlandı.


V2, mevcut verinin yeniden analiziyle güçlendirilmiş öğretici rapordur. Yeni tesis koşusu veya denetleyici ayarı yapılmadı. Sadece metinle kapanamayacak gürbüzlük, donanım ve fiziksel zarf talepleri açık deney ihtiyacı olarak bırakıldı. Aşağıdaki yanıtlar eleştiriyi reddetmek için değil, hangi iddianın hangi kanıtla desteklendiğini netleştirmek için hazırlanmıştır.


Hakem rolü | Odak | Bulgu

Endüstri mühendisi | Pratik anlam, eyleyici, başlangıç ve gerçek zaman | E1-E6

Kontrol teorisi akademisyeni | Türetim, kararlı ters, varsayım ve kararlılık | T1-T6

Yeni doktoralı araştırma asistanı | Metrik duyarlılığı, açıklık ve tekrarlanabilirlik | A1-A6

İzleme yerleri bölüm numarasıyla verilmiştir. Ana metin düzeltmeleri V2’nin ilk 19 bölümüne işlenmiş, yeni hesaplar bölüm 20-27’de toplanmıştır. Özgün 44 denklemin numarası korunur; ek türetimler bunlardan sonra numaralanır.



# 1. Endüstri mühendisi | 1/3



## E1 - İyileşme ile ürün gereksinimini sağlama ayrılmalı.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 12 ve 18: yüzde RMSE sıralaması var; kabul gereksinimi tanımlanmamış.


<b>Yazar yanıtı:</b> Kabul. Nominal hıza göre tepe yüzdesi ve PI’ye göre mutlak tepe/RMSE kazancı eklendi. UDE tepe kazancı 9000/9500 rpm’de 1.300/2.068 rpm. Ürün kabul bandı verilmediği için yeterlilik sonucu çıkarılmıyor.


<b>Düzeltmenin yeri:</b> V2 bölüm 23; bölüm 18 kapsam cümlesi.


<b>Doğrulama / açık iş:</b> Kayıtlı sonuçlardan hesaplandı; ürün kabul kararı açık gereksinim bekler.



## E2 - Sınırlandırılmış yakıt komutu fiziksel valf çıkışı değildir.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 3.3 ve 11; CSV kayıtlarında DOB_command ile Wf eşit, ek yakıt bozucusu sıfır.


<b>Yazar yanıtı:</b> Kabul. Değerlendirme aralığında iki sinyalin en büyük farkı on koşuda da sıfır. Bu ideal arayüz ayrı belirtildi; valf bant genişliği, ölü bölge ve fiziksel değişim hızı sınırı test edilmedi.


<b>Düzeltmenin yeri:</b> V2 bölüm 3.4 ve 24-27.


<b>Doğrulama / açık iş:</b> Eşitlik CSV’den doğrulandı. Fiziksel eyleyici modeliyle yeni deney yapılmadı.



# 1. Endüstri mühendisi | 2/3



## E3 - 30 s’de denge kilitleme genel saha başlangıç algoritması değildir.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 11.1; DOB.start=30, enableTime=2. Son yerleşme kontrolü 55-60 s aralığında.


<b>Yazar yanıtı:</b> Kabul. İşlem senaryoya özgü hazırlık protokolü olarak yeniden tanımlandı. Düşük ivme, küçük hata, kararlı yakıt ve bekleme süresiyle koşullu denge kabulü; hata halinde PI’ye geçiş önerildi, uygulanmış özellik olarak sunulmadı.


<b>Düzeltmenin yeri:</b> V2 bölüm 11.1 ve 27.


<b>Doğrulama / açık iş:</b> Belge düzeltildi; yük altında etkinleştirme ve yeniden başlatma testleri açık iş.



## E4 - Ayar ve yük adaleti sınırları seçim tablosuna taşınmalı.


<b>Önem:</b> Orta-yüksek. <b>Bulgu ve kanıt:</b> 9500 rpm mutlak yükü %62.528 daha büyük; aynı kutup parametresi etkin bantları eşitlemiyor.


<b>Yazar yanıtı:</b> Kabul. Seçim ve sonuç ifadeleri bu sabit ayarlar, yük profilleri ve belirtilen toparlanma bandıyla sınırlandı. Hız, yük, filtre ve telafi sınırlaması etkileri ayrı deneylerle yalıtılmadı.


<b>Düzeltmenin yeri:</b> V2 bölüm 18, 20-21 ve 25-26.


<b>Doğrulama / açık iş:</b> Analitik bant açıklaması ve mevcut kayıt analizi eklendi; eşit güç testi yapılmadı.



# 1. Endüstri mühendisi | 3/3



## E5 - Çekirdek durum sayısı gerçek zaman maliyeti değildir.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> Bölüm 10 ve GZFT: 1/2/3 durum; hedef işlemci ölçümü ve kod üretim kanıtı yok.


<b>Yazar yanıtı:</b> Kabul. Durum sayısının trim, sınırlar, gözetim ve sensör arayüzünü kapsamadığı belirtildi. Matrisler çevrim dışında hazırlanabilir; 15 ms örnek süresi kanıtlanmış en kötü yürütme süresi değildir.


<b>Düzeltmenin yeri:</b> V2 bölüm 27.


<b>Doğrulama / açık iş:</b> SIL/PIL/HIL, tek duyarlık ve hedefte zamanlama ölçümleri açık iş.



## E6 - Hız başarımının kontrol eforu karşılığı gösterilmeli.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> summary.json yakıt/marj içeriyor; rapor esas olarak hız ölçütlerini vurguluyor.


<b>Yazar yanıtı:</b> Kabul. Yakıt toplam değişimi, örneklenmiş en büyük değişim hızı, IAE ve minimum marj eklendi. GPIO yakıt toplam değişimini PI’ye göre yaklaşık %2.77/%3.58 artırıyor. Bu gösterge yakıt tüketimi veya aşınma modeli değildir.


<b>Düzeltmenin yeri:</b> V2 bölüm 23-24 ve 27.


<b>Doğrulama / açık iş:</b> Kayıtlarla tamamlandı; termal zarf ve bakım etkisi doğrulanmadı.



# 2. Kontrol teorisi akademisyeni | 1/3



## T1 - Aynı ω ile gözlemcilerin bantları eşit değildir; türetim gerekir.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 7-9: aynı -ω kutupları, fakat farklı mertebe ve pay polinomları.


<b>Yazar yanıtı:</b> Kabul. İdeal normalize model için d→d̂ aktarımları türetildi: LESO ω²/(s+ω)², UDE ω/(s+ω), GPIO (3ω²s+ω³)/(s+ω)³. DC’ye göre -3 dB frekansları yaklaşık 0.322/0.500/0.821 Hz; GPIO büyüklük tepesi 1.299. Bunlar tam gaz türbini bantları değildir.


<b>Düzeltmenin yeri:</b> V2 bölüm 21.


<b>Doğrulama / açık iş:</b> Analitik ek; yeni benzetim gerektirmedi.



## T2 - Nedensellik yanında kararlı terslenebilirlik sayısal gösterilmeli.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 6.3; Q gecikmeleri açıklıyor, fakat C sıfır yarıçapları gösterilmiyor.


<b>Yazar yanıtı:</b> Kabul. z-düzleminde A kutup yarıçapı 0.977742 ve C sıfır yarıçapı 0.952616 hesaplandı. Q kutbu 0.953969; açılmış ters filtre paydası da birim çember içinde. q ile z kök gösterimi açıklandı. Sonuç yalnız nominal filtreye aittir.


<b>Düzeltmenin yeri:</b> V2 bölüm 22.


<b>Doğrulama / açık iş:</b> Tam duyarlıklı kayıtlı katsayılarla doğrulandı; doğrusal olmayan kapalı çevrim garantisi verilmedi.



# 2. Kontrol teorisi akademisyeni | 2/3



## T3 - B_eq düzeltmesi ve b_0 seçimi birer tasarım varsayımıdır.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 2 ve 6.2: son B katsayısı değiştirilir; bir-adımlı katsayı sürekli giriş kazancı alınır.


<b>Yazar yanıtı:</b> Kabul. Son katsayı değişimi %0.041692 olsa da sıfır frekans yapısını değiştirdiği belirtildi. b_0, doğrulanmış yerel Jacobian değildir; 9500 rpm’de yeniden tanılanmadı. Denklem türetimi ile fiziksel model doğrulaması ayrıldı.


<b>Düzeltmenin yeri:</b> V2 bölüm 22; bölüm 2 uyarısı korunuyor.


<b>Doğrulama / açık iş:</b> Metin ve sayısal büyüklük eklendi; düzeltilmiş modelin bağımsız öngörü başarımı yeniden sınanmadı.



## T4 - Kısmi telafi ve PI ile kapalı çevrim, ideal tam DOB iptali değildir.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 4 ideal u=u_c-d̂; gerçek uygulama g=0.25, sınır ve PI kullanıyor.


<b>Yazar yanıtı:</b> Kabul. Doyumsuz, denge sonrası ideal LTI açıklamada P=P_n(1+Δ) için iç payda 1+gQΔ verildi; PI kapanınca 1+PK+gQΔ oluşur. Bu cebir koşulludur; belirsizlik sınırı veya gürbüz kararlılık ispatı yoktur.


<b>Düzeltmenin yeri:</b> V2 bölüm 21.


<b>Doğrulama / açık iş:</b> Analitik açıklama eklendi; sertifikalı/gürbüz kararlılık sonucu açık bırakıldı.



# 2. Kontrol teorisi akademisyeni | 3/3



## T5 - Aran bağı, UDE başlangıcı ve bozucu tanımı açık tutulmalı.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> Bölüm 5 ayrı yaklaşımı doğru ayırıyor; UDE Laplace cebri sıfır-durum aktarımı iken z(0)=0 ve ilk r sıfır olmayabilir.


<b>Yazar yanıtı:</b> Kısmen kabul. Aran’ın yöntemiyle özdeşlik iddiası zaten yoktu; ayrım korundu. UDE aktarımının sıfır-durum ifadesi olduğu ve başlangıç geçişinin hazırlık protokolünde ele alındığı eklendi. Bozucu saf şaft gücü olarak yorumlanmıyor.


<b>Düzeltmenin yeri:</b> V2 bölüm 8.2, 20 ve 27.


<b>Doğrulama / açık iş:</b> Denklem kapsamı düzeltildi; yeni gözlemci başlangıç tasarımı yapılmadı.



## T6 - Bağımsız tekrar denetimi bütün DOB kollarını kapsamıyor.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> verification.json: observer_replay alanı yalnız LESO/UDE/GPIO kayıtlarında var; DOB için moment denetimi var.


<b>Yazar yanıtı:</b> Kabul. 6.2×10⁻¹⁴ lbm/s üst sınırının yalnız altı düşük mertebeli gözlemci koşusuna ait olduğu açıklaştırıldı. DOB ters filtre için burada yapılan kontrol katsayı/kutup denetimidir; bağımsız zaman alanı tekrar sonucu iddia edilmez.


<b>Düzeltmenin yeri:</b> V2 bölüm 19.1 ve 20.


<b>Doğrulama / açık iş:</b> Kanıt kapsamı düzeltildi; DOB zaman alanı tekrar denetimi açık iş.



# 3. Yeni doktoralı araştırma asistanı | 1/3



## A1 - En hızlı yöntem sonucu toparlanma bandına duyarlı olabilir.


<b>Önem:</b> Yüksek. <b>Bulgu ve kanıt:</b> Bölüm 14-18: ±1 rpm seçimi var fakat eşik duyarlılığı yok.


<b>Yazar yanıtı:</b> Kabul. Aynı CSV’ler ±0.5, ±1 ve ±2 rpm ile tekrar değerlendirildi. 9000 rpm ±0.5 bandında DOB bütün olaylarda en hızlı/eşitken ±1 bandında GPIO öne çıkar. 9500 rpm ±2 bandında GPIO ilk beş olayda en hızlıdır.


<b>Düzeltmenin yeri:</b> V2 öz, bölüm 14 ve 18; bölüm 25-26.


<b>Doğrulama / açık iş:</b> 180 olay/bant kaydı üretildi; yeni tesis koşusu yapılmadı.



## A2 - Hata işareti, birimler ve örnek sayısı tek yerde toplanmalı.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> Kontrol hatası N_istek-N_s; skor N-N_istek. Değerlendirme 90 s, toplam koşu 150 s.


<b>Yazar yanıtı:</b> Kabul. Denetim/skor işareti korundu; 10001 toplam ve 6001 değerlendirme örneği ayrıldı. IAE’nin uç noktalar dahil dikdörtgen toplamı olduğu belirtildi. K_p birimi (lbm/s)/rpm; K_i birimi (lbm/s)/(rpm·s); b_0 birimi (rpm/s)/(lbm/s).


<b>Düzeltmenin yeri:</b> V2 bölüm 12 ve 22.


<b>Doğrulama / açık iş:</b> Mevcut kayıt/denklem açıklaması; 60 özgün toparlanma ve 30 ana skor yeniden eşleşti.



# 3. Yeni doktoralı araştırma asistanı | 2/3



## A3 - Tekrarlanabilirlik için başlangıç koşulları ve yöntem seçimi eksiksiz olmalı.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> Yalnız 2/3/4 yöntem numarası verilmiş; PI ve DOB seçimi runner içinde farklı.


<b>Yazar yanıtı:</b> Kabul. method=1 ile mevcut DOB, aynı seçimde DOB.gain=0 ile PI açıklaması eklendi. Model önce yüklenmeli; önceden hesaplanan yüksüz güç referansı gereklidir. Dondurulmuş verinin yeniden analizi ile yeni benzetim yolu ayrıldı.


<b>Düzeltmenin yeri:</b> V2 bölüm 19.3 ve 27.


<b>Doğrulama / açık iş:</b> Kod değiştirmeden kullanım açıklaması ve kaynak bütünlüğü eklendi.



## A4 - Tablolar sonuçların tamamını ve yorum gücünü göstermiyor.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> IAE tanımlı fakat ana tabloda yok; UDE-GPIO IAE farkı çok küçük.


<b>Yazar yanıtı:</b> Kabul. IAE ve kontrol eforu eklendi. UDE-GPIO IAE farkları yaklaşık 0.00985 ve 0.01825 rpm·s; bu farkın mühendislik/statistiksel anlamlılığı iddia edilmiyor. Sayısal sıralama ile pratik önem ayrıldı.


<b>Düzeltmenin yeri:</b> V2 bölüm 23-24.


<b>Doğrulama / açık iş:</b> Kayıtlı sonuçlarla tamamlandı; tekrarlı/gürültülü deney yapılmadı.



# 3. Yeni doktoralı araştırma asistanı | 3/3



## A5 - Hakem değişiklikleri ana metne de işlenmeli ve izlenmeli.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> V1 raporu 30 sayfa; yalnız ek bir açıklama eski genellemeleri düzeltmez.


<b>Yazar yanıtı:</b> Kabul. Öz ve karar cümlelerine ±1 rpm kapsamı eklendi; eyleyici, tekrar denetimi ve yöntem seçimi metinleri düzeltildi. Ek bölüm 20-27 yeni analizi ayrıntılandırır. V1 PDF ve kaynak betiği korunur.


<b>Düzeltmenin yeri:</b> V2 ana metin ve bölüm 20; bu cevap dosyasındaki her bulgu.


<b>Doğrulama / açık iş:</b> Düzeltme kayıtları ve SHA-256 bütünlüğü oluşturuldu.



## A6 - Kanıtlanmamış iyileştirmeler kapatılmış yorum olarak sunulmamalı.


<b>Önem:</b> Orta. <b>Bulgu ve kanıt:</b> Gürültü, belirsizlik, sıcaklık, hedef zamanlama ve eşit mutlak yük testleri yok.


<b>Yazar yanıtı:</b> Kabul. Metin düzeltmesi ile yeni deney gerektiren açık araştırma işleri ayrıldı. Üç rol yapay zekâ destekli değerlendirmedir; iki paralel inceleme sınır nedeniyle ana oturumda tamamlandı. Bağımsız insan hakem kabulü iddia edilmez.


<b>Düzeltmenin yeri:</b> V2 bölüm 20 ve 27; cevap raporu başlangıç ve sonuç.


<b>Doğrulama / açık iş:</b> Mevcut kapsam tamamlandı; ürün doğrulaması ve yeni deneyler açık iş olarak kaldı.



# Düzeltme sonrası değerlendirme ve açık işler


Bu incelemenin sonucu, raporun mevcut deterministik benzetimler için öğretici bir teknik kayıt olarak güçlenmesidir. Bağımsız hakem kabulü veya sahaya hazır denetleyici sonucu verilmez. Ana sonuçların doğruluğu ile kapsamının sınırlılığı birbiriyle çelişmez: GPIO RMSE, UDE tepe açısından öndedir; toparlanma liderliği ise belirtilen banda bağlıdır.


Tamamlanan | Kanıt

Ana skor kontrolü | 30 skor ham CSV’den 10⁻⁹ toleransla eşleşti.

Özgün olay kontrolü | 60 toparlanma değeri 10⁻⁹ toleransla eşleşti.

Eşik duyarlılığı | 3 bant × 6 olay × 10 koşu = 180 kayıt.

Nominal filtre kontrolü | A kutupları, C sıfırları, Q ve ters payda birim çember içinde.

Efor değerlendirmesi | Yakıt TV, örneklenmiş en büyük eğim, IAE ve marj tabloları.

Belge kontrolü | V1 korunarak V2 ve bu yanıt ayrı üretilir; sayfalar görsel denetlenir.


## Yeni deney gerektiren açık işler


Eşit mutlak yük ve bağımsız ayar karşılaştırması; sensör gürültüsü/gecikmesi; eyleyici dinamiği ve yakıt değişim hızı sınırı; termal/kompresör işletim zarfı; yük altında denge kabulü; DOB’un bağımsız zaman alanı tekrar testi; tek duyarlık ve hedefte en kötü işlem süresi. Bunların hiçbirinin yalnız rapor metni değiştirilerek doğrulandığı iddia edilmez.


Öncelik önerisi: önce ürünün tepe ve toparlanma bandını belirleyin; sonra eşlenmiş yük/efor koşullarında gürültü ve eyleyici sınırıyla tekrar karşılaştırın. Bu aşamadan sonra UDE, GPIO veya DOB seçiminin hedef işlemci maliyeti ölçülmelidir.
