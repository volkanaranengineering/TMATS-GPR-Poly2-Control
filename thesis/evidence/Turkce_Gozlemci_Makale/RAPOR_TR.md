
# Gaz Türbininde Yük Değişimlerine Karşı Hızın Korunması


<b>DOB, LESO, UDE ve GPIO yöntemlerinin 9000 ve 9500 rpm çalışma noktalarında karşılaştırılması</b>


Görselli mühendislik makalesi | V2 temelli genişletilmiş sürüm | 13 Eylül 2026 | T-MATS projesi



## Öz


Bu çalışma, mevcut oransal-integral (PI) hız denetleyicisini değiştirmeden bozucu kestirimiyle güçlendiren dört yapıyı açıklar: tanılanmış modele dayalı bozucu gözlemci (DOB), doğrusal genişletilmiş durum gözlemcisi (LESO), belirsizlik ve bozucu kestiricisi (UDE) ve genelleştirilmiş oransal-integral gözlemci (GPIO). Sürekli zaman denklemleri, sayısal parametrelerin kökenleri, ayrık zaman gerçekleştirimleri ve Simulink işlem sırası adım adım verilir. Volkan Aran’ın veriye dayalı DOB yaklaşımı ile gaz türbininde kullanılan ters filtre uyarlaması arasındaki bağ ayrıca incelenir.


Doğrusal olmayan T-MATS benzetimlerinde hız 9000 veya 9500 rpm’de tutulurken, ilgili çalışma noktasındaki brüt türbin gücünün %10’u şafttan çekilir. Yükün uygulanması ve kaldırılması 0.30, 1.50 ve 3.00 saniyelik rampalarla yapılır. On koşunun tamamı sayısal geçerlilik denetimlerini sağlar. GPIO her iki hızda en düşük kök ortalama kare hatayı, UDE en düşük tepe hız hatasını verir. ±1 rpm bandında 9500 rpm’de DOB altı olayın tamamında en kısa veya eşit en kısa toparlanma süresine ulaşır. V2’de ±0.5 ve ±2 rpm bantları da aynı kayıtlardan değerlendirilmiş, toparlanma sıralamasının bant seçimine bağlı olduğu gösterilmiştir. Dolayısıyla seçim, başarım gereksinimine bağlıdır.



## Kapsam ve okuma sırası


İçerik | Bölümler

Görselli problem tanıtımı ve araştırmanın özeti | Giriş

Problem, parametreler ve deney kurulumu | 1-3

Aran’ın yaklaşımı, DOB ve diğer gözlemciler | 4-9

Ayrık gerçekleştirim ve denge düzeltmesi | 10-11

Sonuçlar, grafikler ve toparlanma tabloları | 12-15

GZFT değerlendirmeleri ve izlenecek yol | 16-19

Ek analiz, geçerlilik ve uygulamaya geçiş | 20-27

<b>Anahtar sözcükler:</b> gaz türbini, PI denetimi, bozucu bastırma, veriye dayalı model, DOB, LESO, UDE, GPIO.


Makale, mühendislik lisans düzeyindeki bir okuyucu için görselli problem tanıtımıyla başlar. V2’deki düzeltilmiş teknik içerik, sayısal tablolar ve ek analizler korunur. Yeni giriş, fiziksel problemden yöntem seçimine geçişi açıklar. Sayısal sonuçlar korunmuştur. Yeni benzetim veya yeniden ayar yapılmamıştır. Kaynak eserlerin özgün adları ve yazılım tanımlayıcıları izlenebilirlik için korunur.



# Giriş: Şaft yükü değişirken hız nasıl korunur?


Bir gaz türbini bir jeneratörü, pompayı veya başka bir mekanik yükü döndürürken yükün artması, şafttan daha fazla güç istenmesi demektir. Türbin o anda aynı gücü üretmeye devam ederse eksik enerji dönen parçaların kinetik enerjisinden karşılanır; şaft yavaşlar. Yük kaldırıldığında ise kısa süreli güç fazlası oluşur ve hız yükselir. Bu makalenin problemi, bu geçişlerde hız sapmasını küçük tutup hedef hıza çabuk dönmektir.


<i>Şekil G1. Tek şaftlı örneğin kavramsal enerji akışı. Mavi oklar gaz yolunu, turkuaz bağlantı mekanik şaftı, turuncu oklar yakıt ve ek yükü gösterir. Bu özgün şema bir Simulink ekran görüntüsü değildir; araştırmada kullanılan bağlantı fikrini açıklar.</i>



## Enerji dengesiyle sezgisel açıklama


Türbin gazın enerjisini mekanik güce dönüştürür; kompresör bu gücün bir bölümünü tüketir. Geriye kalan güç, dış yük ve dönme enerjisindeki değişim arasında paylaşılır. SI birimlerinde bu düşünce şöyle yazılır:


$$\frac{d}{dt}\left(\frac{J\Omega^2}{2}\right)=P_t-P_c-P_L,\qquad \Omega=\frac{2\pi N}{60}$$ (G1)

J atalet, Ω açısal hız, N rpm cinsinden hızdır. Burada P_c pozitif kompresör tüketimidir; ilerideki T-MATS denkleminde kompresör gücü işaretli kaydedilir.


<b>Araştırma sorusu:</b> Mevcut PI hız denetleyicisini koruyup ölçülen hız ve yakıt bilgisinden ek bir düzeltme üretirsek yükün oluşturduğu hız sapmasını ne kadar azaltabiliriz? Jeneratör ve pompa, sorunun kullanım örnekleridir; benzetimde ayrıntılı elektrik veya pompa modeli yerine doğrudan şaft gücü çekişi uygulanmıştır.



# Giriş: T-MATS neden bu çalışmanın merkezinde?


T-MATS, “Toolbox for the Modeling and Analysis of Thermodynamic Systems” adının kısaltmasıdır. NASA’nın MATLAB/Simulink ortamı için geliştirdiği açık kaynak araç kutusu, termodinamik bileşenleri ve denetim modellerini aynı benzetimde birleştirir. Kompresör, yanma odası, türbin ve şaft gibi modüler bileşenler; akış uyumunu sağlayan sayısal çözücüyle birlikte çalışır [7].


<i>Şekil G2. Bu araştırmanın sayısal deney düzeni. Tesis, deney koşulları ve denetim seçeneği ayrı tutulur; aynı yük altında farklı denetleyicilerin yanıtı kaydedilir. Şema kavramsal iş akışıdır, çözücü yürütme sırasının birebir gösterimi değildir.</i>


Kullanıcı kılavuzunun 7.3 bölümü dinamik gaz türbini örneğini, 7.3.2 bölümü ise şaft hızından geri beslenen basit PI eklenmesini açıklar [7]. Bu projede standart GasTurbine_Dyn_Template modelinin GPT kopyasından ilerlenmiş; ilave şaft yükü, veri kaydı ve gözlemci kolları eklenmiştir. Karşılaştırılan sürüm GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT modelidir.


T-MATS burada bir sanal deney tezgâhıdır: yük büyüklüğünü ve süresini tekrarlanabilir biçimde değiştirip hız, yakıt ve çözüm tutarlılığını incelemeyi sağlar. Kılavuz, basit PI örneğinin gerçek motorlardaki çok değişkenli kısıtları tek başına temsil etmediğini de belirtir [7, s. 36]. Bu nedenle sonuçlar belirli bir fiziksel motorun deneysel doğrulaması olarak sunulmaz.



# Giriş: PI’ye gözlemci eklemek neyi değiştirir?


PI denetleyicisinin oransal kısmı o anki hız hatasına, integral kısmı zaman içinde biriken hataya göre yakıtı değiştirir. Yük etkisini doğrudan ölçmese de hata üzerinden düzeltir. Gözlemci ise “uygulanan yakıtla beklenen hız davranışı” ile ölçümü karşılaştırıp açıklanamayan etkiyi kestirir. Böylece aynı PI’nin çıkışına ek bir yakıt düzeltmesi yapılabilir.


<i>Şekil G3. Ortak denetim fikri. PI korunur; gözlemcinin sınırlı telafisi yakıt komutuna ek etki yapar. Sensör hızı ve son sınırlandırılmış yakıt gözlemciye girer. Ayrıntılı örnekleme ve nedensel işlem sırası bölüm 10-11’dedir.</i>


Yöntem | Temel fikir

DOB | Tanılanmış dinamik modelin tersini kullanarak eşdeğer giriş artığını kestirir.

LESO | Bilinmeyen etkiyi ek durum sayar; hız ile bozucuyu birlikte kestirir.

UDE | Model artığını bir süzgeçle kestirir; bu uygulamada tek temel durum kullanır.

GPIO | Bozucuya ek olarak değişim eğimini kestirir; rampalı yükler için bir adaydır.

Hiçbiri gelecekteki yükü bilen bir öngörücü değildir. Kestirim; dış yükün yanında model hatası ve sensör etkilerini de içerir. Bu çalışmada telafinin yalnız %25’i kullanılır ve etkisi sınırlandırılır. Amaç PI’yi değiştirmekten önce, gözlemci eklemenin hangi başarım ölçütüne katkı sağladığını görmek ve maliyetini anlamaktır.



# Giriş: Bir yük olayı nasıl okunur?


Deneylerde hız isteği 9000 veya 9500 rpm’de sabittir. Her hızda önce yüksüz durumdaki brüt türbin gücü bulunur; bu gücün %10’u şafttan çekilir. Bu tanım 9000 rpm’de 0.879 MW, 9500 rpm’de 1.429 MW ek yük verir. Yükün yükselme ve azalma süreleri 0.30, 1.50 ve 3.00 s seçilir; arada yük sabit tutulur.


<i>Şekil G4. Gerçek kayıtların 9000 rpm’deki ilk 0.30 s yük uygulaması. Üstte güç çekişi, altta hız sapması görülür. Gri alan yük rampası, yeşil alan ±1 rpm bandıdır. Yük bu pencerenin sonunda hâlâ uygulanmaktadır.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/giris_yuk_olayi.png)

Önce yük yükselir ve hız düşer. PI yakıtı artırdıkça hız geri gelir. Gözlemci ekleri, ilk sapmanın büyüklüğünü veya geri dönüşün biçimini değiştirebilir. Bu örnekte UDE daha küçük tepe sapması verirken GPIO ±1 rpm bandına daha erken döner. İki ifade farklı başarım özelliklerini anlatır.


Ölçüt | Mühendislik anlamı

Tepe hız hatası | En büyük anlık sapma ne kadar?

RMSE | Bütün deney boyunca tipik hata ne kadar? Büyük hatalar daha fazla ağırlık alır.

Toparlanma süresi | Belirlenen hata bandına ne zaman dönülüp orada kalınıyor?

Yakıt hareketi | İyileşme ne kadar ek komut hareketi gerektiriyor?


# Giriş: Araştırma ne gösteriyor?


<i>Şekil G5. Aynı hızdaki temel PI’ye göre hata azalması. GPIO ortalama karesel hata, UDE tepe hata açısından öne çıkar. PI, kendi referansı olduğu için sıfır azalma ile gösterilir. Kaynak: değiştirilmeyen on benzetim kaydı.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/giris_iyilesme.png)

<b>Tek bir genel kazanan yoktur.</b> GPIO, iki hızda RMSE’yi PI’ye göre yaklaşık %20 azaltır. UDE en büyük hız sapmasını yaklaşık %12 ve %11 azaltır; mutlak farklar sırasıyla 1.30 ve 2.07 rpm’dir. Daha küçük tepe ile daha kısa toparlanmanın aynı yöntemle sağlanması zorunlu değildir.


Toparlanma sonucunda kabul bandı belirleyicidir. ±1 rpm bandında 9500 rpm’de DOB bütün olaylarda en hızlı veya eşit en hızlıdır. Bant ±0.5 rpm’ye daraltıldığında DOB iki hızda da bu özelliği gösterir; ±2 rpm’ye genişletildiğinde GPIO öne çıkabilir. Bu yüzden “ne kadar hızlı?” sorusundan önce “hangi hata bandına?” sorusu yanıtlanmalıdır.


İyileşmenin bir karşılığı da vardır: GPIO’nun yakıt toplam değişimi PI’ye göre yaklaşık %2.77 ve %3.58 artar. Ayrıca iki hızda aynı yüzde yük, aynı mutlak güç değildir. Gürültüsüz ve ideal yakıt arayüzlü bu deneyler, gerçek valf ve işlemci yeterliliğini kanıtlamaz; bir sonraki tasarım ve doğrulama adımını seçmeye yardımcı olur.



## Makalenin devamı


Bölüm 1-3 problemi ve deney parametrelerini kesinleştirir; bölüm 4-11 gözlemcileri türetir ve temel Simulink bloklarına bağlar. Bölüm 12-18 yanıtları ve yöntem seçimini, bölüm 19-27 doğrulama, efor ve kabul bandı duyarlılığını verir. Yeni giriş şekilleri G1-G5 olarak adlandırılmıştır; V2’deki teknik denklem ve bölüm numaraları izlenebilirlik için korunmuştur.



# 1. Problem tanımı ve teknik gösterim



## 1.1 Bozucuyu neden kestiriyoruz?


Şafttan aniden güç çekildiğinde mekanik güç dengesi bozulur ve hız düşer. PI denetleyicisi bu düşüşü ölçtükten sonra yakıtı artırır. Gözlemci, ölçülen hız ile uygulanmış yakıt arasındaki model uyumsuzluğunu kullanarak ek bir düzeltme üretir. Amaç, mevcut geri beslemenin üzerine sınırlı bir bozucu telafisi eklemektir.


Gözlemci yalnızca dış yükü görmez. Model hataları, ihmal edilen dinamikler ve ölçüm etkileri de artık sinyalin içinde yer alır. Bu nedenle yakıt birimindeki kestirim, doğrudan ölçülmüş bir şaft gücü olarak yorumlanmamalıdır. Gerçek ivme ve yük kayıtları doğrulama içindir; gözlemciye ayrı bir gerçek-bozucu ölçümü verilmez.


Büyüklük | Anlamı

P_L: şaft yükü | Dışarı çekilen fiziksel mekanik güç; hp veya MW.

d: eşdeğer bozucu | Giriş/yakıt biriminde ifade edilen toplam artık etki.

c: telafi | PI çıkışından çıkarılan sınırlı düzeltme. Negatif c, yakıtı artırır.

N ve N_s | Sırasıyla gerçek şaft hızı ve sensörden gelen hız.


## 1.2 Yöntemler arasındaki ortaklık


Tüm yöntemlerde aynı tesis, sensör, PI kazançları, yakıt sınırları, telafi kazancı ve rampa süreleri kullanılır. DOB daha ayrıntılı seyrek ARX modelini korur. Diğer üç gözlemci yaklaşık bir giriş kazancından hareket eder. LESO iki, UDE bir, GPIO üç temel durum taşır; GPIO bozucunun eğimini de kestirir.


Aynı kutup frekansı parametresi, farklı yapılarda aynı etkin bant genişliği anlamına gelmez. Bu karşılaştırma, sabit ayarlı somut uygulamaların karşılaştırmasıdır. Tek başına gözlemci yapısının üstünlüğünü veya en iyi ayarlanmış denetleyiciyi belirlemez.



## 1.3 Gösterim


Bu raporda q bir örnek gecikmesini gösterir: qx[k] = x[k-1]. s sürekli zaman Laplace değişkenidir. r, normalize hız değişkenidir; DOB kutbu ile karışmaması için ayrık gözlemci kutbuna α adı verilmiştir. Denklem numaraları bu Türkçe rapora aittir; tezdeki numaralar metinde ayrıca belirtilir.



# 2. Parametrelerin tanımı ve kökeni


Aşağıdaki değerler deneyin tam tanımıdır. Bir yayının zorunlu kıldığı veya eniyilenmiş değerler değildir. Devralınan tesis ayarları, tanılama sonuçları ve gözlemci tasarım tercihleri ayrı gösterilmiştir. İki hız arasında yeniden ayar yapılmaz.


Parametre | Değer | Köken / işlev

K_p; K_i | 0.025; 0.05 | PI maskesi: 0.05/2 ve 0.1/2

I(0) | 3 lbm/s | PI_IC_M başlangıç integrali; denge yakıtı değil

T_s | 0.015 s | Veri ve çözüm aralığı

Sensör | Kazanç 1; τ = 0.05 s; 0-20000 rpm | Mevcut model; gürültü kapalı

N_0; u_0 | 9000 rpm; 0.9810869146824126 lbm/s | Tanılama ofsetleri; iki hızda sabit

b_0 | 361.94069376173167 | İlk sıfırdan farklı ARX yakıt katsayısı

f_c; ω | 0.5 Hz; π rad/s | Korunan gözlemci kutup ayarı

g; telafi sınırı | 0.25; ±0.15 lbm/s | Kısmi telafi ve etki sınırı

Yakıt aralığı | 0.2-4 lbm/s | Ortak eyleyici sınırı

Denge / etkinleştirme | 30 s’de tutma; 2 s’de devreye alma | Yumuşak geçiş tercihi

İstek eğim sınırı | ±150 rpm/s | Mevcut hız isteği sınırlayıcısı

Yük ve rampalar | %10; 0.30 / 1.50 / 3.00 s | İstenen genlik ve deney süreleri

Hazırlık isteği ilk 5 saniye 10000 rpm’dir; kaynak istek 5-10 saniye arasında hedefe iner. 9000 rpm için istenen -200 rpm/s eğim, 150 rpm/s sınırlayıcı nedeniyle uzar. 9500 rpm’de -100 rpm/s istek bu sınıra takılmaz. Her iki koşulun da 60 saniyede değerlendirme başlamadan önce yerleştiği kayıtlarla doğrulanmıştır.


b_0 bir adımlı ARX katsayısının yaklaşık sürekli zaman giriş kazancı olarak kullanılmasıdır. Sensör dahil yeni bir yerel tanılama değildir. 9500 rpm verileriyle güncellenmemiştir.



# 3. Yük deneyi ve PI arayüzü



## 3.1 Çalışma noktasına göre %10 yük


Önce dış şaft yükü sıfırken hedef hızda yerleşilir. Mutlak 55-60 saniye arasındaki türbin gücü ortalaması P_0 olarak alınır. Yüzde hesabı brüt türbin gücüne dayanır; sıfıra yakın net şaft gücüne dayanmaz. Eski %20 veya %30 deneylerinden kalmış yük değeri kullanılmaz.


$$P_{L,\max}=0.10P_0,\qquad 1\,\mathrm{hp}=0.7456998715822702\,\mathrm{kW}$$


Hız | P_0 (hp) | P_L,max (hp) | P_L,max (MW)

9000 rpm | 11789.245211 | 1178.924521 | 0.879123864

9500 rpm | 19160.793887 | 1916.079389 | 1.428820154

$$S(x)=\min(1,\max(0,x)),\quad P_L(t)=0.10P_0\sum_{j=1}^{3}\left[S\!\left(\dfrac{t-a_j}{T_j}\right)-S\!\left(\dfrac{t-b_j}{T_j}\right)\right]$$


Değerlendirme başlangıcına göre uygulama anları a = [10.005, 30, 60] s; kaldırma anları b = [15, 40.005, 75] s; rampa süreleri T = [0.30, 1.50, 3.00] s’dir. Yük artış eğimi P_L,max / T_j, azalış eğimi bunun ters işaretlisidir.


Rampa (s) | 9000 rpm eğimi (MW/s) | 9500 rpm eğimi (MW/s)

0.30 | 2.930413 | 4.762734

1.50 | 0.586083 | 0.952547

3.00 | 0.293041 | 0.476273


## 3.2 Mekanik denge


$$\dot N=\dfrac{60}{2\pi J}\left[\dfrac{5252.113(P_t+P_c)-5252.11P_L}{N}\right],\qquad J=30$$


Güçler hp, hız rpm cinsindedir; J standart modelin atalet birimi düzenindedir. Kompresör gücü P_c işaretlidir ve güç tüketimi negatiftir. Dönüşüm sabitlerinin küçük farkı mevcut modelden gelir. Ek yakıt yükü karşılayıncaya kadar güç çekişi negatif ivme üretir.



# 3.3 PI ve ortak telafi yasası


$$e_c=N_{\rm istek}-N_s,\quad u_{\rm PI}=K_pe_c+I,\quad \dot I=K_ie_c,\quad I(0)=3$$


K_p = 0.025 ve K_i = 0.05 değerleri korunur. PI sürekli zamanlıdır. Sensörün 0.05 s zaman sabiti geri beslemeyi etkiler. Başarım hesaplarında gerçek hız kullanılır; dolayısıyla grafiklerdeki N - N_istek hata işareti, denetim hatası e_c’nin tersidir.


$$c(t)=\rho(t)\,\mathrm{sat}_{[-0.15,\,0.15]}\!\left[0.25(\hat d-\hat d_{\rm denge})\right]$$


$$u=\mathrm{sat}_{[0.2,\,4]}(u_{\rm PI}-c),\qquad 0\leq\rho(t)\leq1$$


ρ, 30 saniyelik denge kaydı sonrasında 2 saniyede sıfırdan bire çıkan etkinleştirme çarpanıdır. Temel PI koşulunda telafi kazancı sıfırdır. Son sınırlandırılmış yakıt hem tesise hem gözlemciye girer. Böylece gözlemci, uygulanmayan bir yakıt isteği üzerinden kestirim yapmaz.


Negatif giriş eşdeğerli bozucu hız düşürücü etkiyi temsil eder. Negatif kestirimden oluşan negatif c, PI çıkışından çıkarıldığında yakıtı artırır. %25 telafi ve ±0.15 lbm/s sınırı, gözlemci kestirimine sınırlı otorite verir. Tam bozucu iptali hedeflendiği varsayılmamalıdır.



## 3.4 Gerçekleştirim kapsamı


Bu benzetimde sınırlandırılmış yakıt komutu ile gerçek tesis yakıt girişi özdeştir. Ayrı yakıt valfi bant genişliği, ölü bölge veya fiziksel debi değişim hızı sınırı modellenmemiştir; bölüm 24 bu özdeşliği kayıtlardan doğrular.


Yeni gözlemciler Gain, Sum, Mux ve Unit Delay gibi temel Simulink bloklarıyla gerçekleştirilir. Gözlemci çekirdeklerinde S-function veya MATLAB Function kullanılmaz. Bu ifade, özgün T-MATS tesis bileşenlerinin iç yapısını değiştirdiğimiz anlamına gelmez. Bu çalışmada PI’ye ek integral yığılması önleme (anti-windup) mantığı eklenmemiştir; koşular yakıt doyumuna ulaşmamıştır.



# 4. DOB: temel fikir ve literatür kökeni



## 4.1 Nominal ters modelden giriş artığına


Klasik DOB düşüncesi, çıkışı üretebilmek için nominal modelin gerektirdiği giriş ile gerçekte uygulanan girişi karşılaştırır. Aran’ın tezinin 4.1 bölümünde bu çizgi Ohishi, Ohnishi ve Miyachi’nin yük momenti kestirimine dayalı motor denetimi çalışmasına bağlanır [1]. Aynı bölümde ölçüm belirsizliği ve model hatasının dış bozucuyla birlikte toplandığı vurgulanır. Tarihsel atıf burada tez üzerinden verilmektedir.


$$y=P(u+d),\quad y_m=y+n,\quad d_\ell=P_n^{-1}y_m-u$$


$$d_\ell=d+(P_n^{-1}-P^{-1})y+P_n^{-1}n$$


P gerçek tesis, P_n nominal model, d giriş bozucusu, n ölçüm gürültüsüdür. Burada ölçüm y_m = y + n olarak tanımlandığından gürültü terimi artı işaretlidir. Tezdeki ölçüm işareti seçimi farklıdır; bu bir fiziksel fark değil gösterim farkıdır. Nominal model tam doğru olsa bile ölçüm gürültüsü ters model üzerinden kestirime taşınır.



## 4.2 Q filtresinin iki görevi


$$\hat d=Q\left(P_n^{-1}y_m-u\right),\qquad u=u_c-\hat d$$


Ters model tek başına nedensel veya uygulanabilir olmayabilir. Alçak geçiren Q filtresi hem bu gerçekleştirilebilirlik sorununu yönetir hem yüksek frekans bileşenlerini sınırlar. İdeal eşleşmede kestirim Qd olur. Q yaklaşık bir olduğunda düşük frekanstaki bozucu güçlü biçimde bastırılabilir; bant dışında aynı sonuç beklenmez [1,2].


Nominal tersin doğruluğu, gecikme ve filtre bant genişliği birlikte önemlidir. Gözlemci bant genişliğini büyütmek her koşulda iyileşme sağlamaz. Model uyumsuzluğu ve sensör gürültüsü nedeniyle kapalı çevrim davranışı ayrıca değerlendirilmelidir. Aşağıdaki gaz türbini yapısı, bu klasik artık-kestirim ilkesinin veriye dayalı nominal modelle uygulanmasıdır.



# 5. Volkan Aran’ın veriye dayalı DOB yaklaşımı



## 5.1 Tezin amacı ve temel modeli


Aran’ın 2019 doktora tezi, ağır hizmet dizel motorunun hava yolu denetiminde ticari elektronik kontrol birimlerinde uygulanabilecek düşük hesap yüküne sahip bir yapı geliştirir. Tezin 4.2 bölümünde doğrusal nominal kısım sistem tanılama ile elde edilir; doğrusal olmayan etkiler, tanılama hataları ve dış etkiler toplam bozucu içinde ele alınır. Bölüm 6.1’de bu yapı EGR ile kütle hava debisi, VGT ile manifold basıncı denetimine uygulanır [1]. Aran ve Ünel’in 2017 bildirisi aynı araştırma çizgisinin yayın kaydıdır [2].


$$y[k+1]=\hat A x[k]+\hat B u[k]+d_o[k]$$


$$u_d[k]=\dfrac{d_o[k]}{\hat B}=\dfrac{y[k+1]-\hat A x[k]}{\hat B}-u[k],\qquad \hat B\ne0$$


x geçmiş ölçüm ve girişlerden oluşan regresör vektörüdür; fiziksel durumların tamamının doğrudan ölçüldüğü varsayılmaz. d_o çıkış birimindeki model artığı, u_d ise giriş eşdeğeridir. Tezdeki (4.11)-(4.13) denklemlerinin aynı cebirsel ilişkisi burada k+1 gösterimiyle yazılmıştır. Ancak y[k+1] henüz bilinmediğinden bu ifade tek başına anlık uygulanamaz.



## 5.2 Nedensel süzülmüş artık


$$\Delta y[k]=y[k+1]-y[k],\quad \eta[k]=\dfrac{y[k]-\hat A x[k]}{\hat B}-u[k]=u_d[k]-\dfrac{\Delta y[k]}{\hat B}$$


$$\hat u_d=Q(q)\eta,\quad e_{u_d}=(1-Q)u_d+Q\dfrac{\Delta y}{\hat B}$$


Bu düzenleme tezdeki (4.14)-(4.16) çizgisini açık parantezlerle yeniden verir. Süzülen artık, gelecekteki çıkış kullanılmadan hesaplanabilir; fakat bir çıkış artışı terimi taşır. Başarı, bozucu içeriği ve bu terimin frekans özellikleri ile Q seçimine bağlıdır. Bu yüzden kestirimi kusursuz anlık bozucu ölçümü olarak sunmak doğru değildir.



# 5.3 Tezden gaz türbinine aktarımın sınırları


Tezde hava yolu kanalları ayrı denetlenirken aralarındaki fiziksel etkileşim DOB artıklarında temsil edilir. Kestirim, ayrık zamanlı kayar kipli denetleyiciyle birleştirilmiştir; tez ayrıca gerçek motor ve ECU üzerindeki WHTC deneylerini bildirir [1, bölüm 7.6]. Bu kanıt, burada kullanılan gaz türbinine veya PI tabanlı uygulamaya otomatik olarak aktarılmaz.


Bu projede ortak fikir, ölçülen çıktının tanılanmış nominal modelden sapmasını giriş biriminde kestirip temel denetleyiciye eklemektir. Ancak kullanılan kayıtlı DOB, tezin tek-adımlı artık denkleminin birebir kodu değildir. Seyrek ARX ivme modelinden bir hız modeli çıkarılır; sensör dahil edilir ve Q/P_n ters filtre kolu gerçekleştirilir. Kayıtlı karşılaştırmada seçilen yol Mode 2’dir; alternatif artık yolu bu sonuçların kaynağı değildir.


Başlık | Aran’ın tezindeki yaklaşım | Bu gaz türbini uyarlaması

Tesis / eyleyici | Dizel hava yolu; EGR ve VGT | Gaz türbini; yakıt debisi

Çıkış | MAF ve MAP kanalları | Şaft hızı; model kökü ivme ARX’i

Model artığı | Tanılanmış doğrusal model + toplam bozucu | Seyrek ARX hız modeli + sensör uyumsuzluğu

Kestirim | Giriş eşdeğerli artık ve Q süzmesi | (Q/P_n)y - Qv ters filtre yapısı

Temel denetleyici | Ayrık zamanlı kayar kipli yapı | Mevcut sürekli PI

Telafi | Teze özgü kanal yapısı | %25 kazanç, sınır, denge çıkarımı

Kanıt | Tezde benzetim ve gerçek motor deneyleri | Kaydedilmiş T-MATS benzetimleri

Aran’ın GPR tabanlı ileri besleme ve denetim çalışmaları ayrı bir modelleme koludur. Bu rapordaki DOB, GPR kestiricisi kullanmaz. Aynı şekilde sabit ARX katsayılarının kökeni önceki iki aşamalı RLS çalışması olsa da karşılaştırma sırasında çevrim içi RLS güncellemesi yapılmaz.



# 6. Gaz türbini için ARX tabanlı DOB türetimi



## 6.1 Seyrek regresörlerden nominal modele


Önceki chirp tanılaması, ivme çıkış gecikmeleri [1, 2, 4, 6] ve yakıt giriş gecikmeleri [1, 2, 5, 10] olmak üzere sekiz regresör seçmiştir. En büyük gecikme 10 örnek olması, on adet sıfırdan farklı regresör kullanıldığı anlamına gelmez. v = u - u_0 ve a = dN/dt için model aşağıdadır.


$$A(q)a=B(q)v$$


$$A(q)=1-1.894337317304q+0.843546068890q^2+0.073043307628q^4-0.021358276735q^6$$


$$B(q)=361.940693761732q-497.137697864232q^2+147.924362845582q^5-12.732667296544q^{10}$$



## 6.2 Denge kısıtı ve ivmeden hıza geçiş


$$B_{\rm eq}[10]=B[10]-\sum_{i=0}^{10}B[i]=-12.727358743081226$$


Özgün katsayı toplamı -0.005308553463’tür. Yalnızca son yakıt katsayısı düzeltilerek B_eq(1) = 0 sağlanır; sabit girişte sıfır kalıcı ivme kısıtı uygulanır. Bu işlem 9500 rpm’de yeniden tanılama değil, projeye özgü denge düzeltmesidir.


$$P_{N/u}(q)=\dfrac{T_sB_{\rm eq}(q)}{(1-q)A(q)}=\dfrac{B_N(q)}{A(q)},\quad B_N(q)=qC(q)$$


$$B_N[i]=T_s\sum_{j=0}^{i}B_{\rm eq}[j],\qquad i=0,\ldots,9$$


Katsayı indeksi | B_N değeri

0; 1 | 0; 5.429110406426

2, 3, 4 | Her biri -2.027955061538

5, 6, 7, 8, 9 | Her biri 0.190910381146

B_eq içindeki (1-q) çarpanı, ivme integralindeki aynı çarpanla sadeleşir. İlk sıfır katsayı bir örnek giriş gecikmesini temsil eder. C polinomu bu gecikme ayrıldıktan sonra kalan katsayılardır.



# 6.3 Sensör ve nedensel ters filtre


$$H(q)=\dfrac{q(1-p)}{1-pq},\quad p=e^{-T_s/0.05}=0.740818220682$$


$$P_n(q)=H(q)P_{N/u}(q)=\dfrac{q^2(1-p)C(q)}{A(q)(1-pq)}$$


Doğrusal olmayan benzetimde sürekli sensör korunur; H, gözlemci tasarımındaki ayrık yaklaşımdır. Yakıt-hız kolu ile sensör yaklaşımı toplam iki gecikme içerir. Bu gecikmelerin terslenmesi gelecekteki örnekleri gerektireceğinden Q içine iki gecikme konur.


$$\alpha=e^{-2\pi f_cT_s}=0.953969203212,\qquad Q(q)=\dfrac{q^2(1-\alpha)^2}{1-2\alpha q+\alpha^2q^2}$$


$$Q(q)=\dfrac{0.002118834253q^2}{1-1.907938406423q+0.910057240676q^2}$$


$$\dfrac{Q(q)}{P_n(q)}=\dfrac{(1-\alpha)^2A(q)(1-pq)}{(1-p)C(q)(1-2\alpha q+\alpha^2q^2)}$$


$$\hat d=\dfrac{Q}{P_n}(N_s-N_0)-Q(u-u_0)$$


Son ifadede ileri kaydırmalar cebirsel olarak yoktur. Pay ve payda, katsayı dizilerinin evrişimiyle oluşturulur. Tam duyarlıklı polinomlar parameter_derivation.json dosyasındadır. Denge çıkarımı ve ortak telafi yasası bu ham kestirime sonradan uygulanır.



## 6.4 Neden bu yapı çalışabilir?


Nominal model ölçülen davranışı yeterince temsil ettiği frekanslarda, ölçülmüş hızı oluşturmak için gereken ek yakıt artığı kestirilir. Q bu artığın yavaş bileşenlerini geçirir; PI ise kalan hız hatasını düzeltir. Deneydeki yarar bu kapalı çevrim birleşiminin sonucudur. Kararlı nominal filtre kutupları, doğrusal olmayan tüm kapalı çevrim için tek başına kararlılık ispatı oluşturmaz.



# 7. LESO: doğrusal genişletilmiş durum gözlemcisi



## 7.1 Temel fikir ve kaynak bağı


LESO, bilinmeyen dinamikleri toplam bozucu adlı ek bir durum olarak modele katar. Böylece yalnızca yaklaşık giriş kazancı bilinse de hız ve artık etki birlikte kestirilebilir. Yapı, genişletilmiş duruma uygulanan doğrusal Luenberger gözlemcisi olarak okunabilir. Gao’nun bant genişliği parametrelemesi ayarı tek bir frekans üzerinden düzenler [3]; Herbst bu fikrin uygulama ve ayrık zaman boyutlarını öğretici biçimde açıklar [4].


$$y=N_s-N_0,\quad v=u-u_0,\quad \dot y=b_0v+f$$


$$r=\dfrac{y}{b_0},\quad d=\dfrac{f}{b_0},\quad \dot r=v+d,\quad b_0=361.940693761732$$


f; yük, doğrusal olmayanlık, giriş kazancı hatası ve sensör dinamiğinin yaklaşık modelde açıklanmayan etkilerini kapsar. r birimi yakıt biriminin zamanla çarpımına karşılık gelir; d ve v lbm/s birimindedir. Kestirilecek bozucunun yerel olarak yavaş değiştiği kabul edilir.



## 7.2 Hata enjeksiyonu ve kutup seçimi


$$\varepsilon=r-\hat r,\qquad \dot{\hat r}=v+\hat d+l_1\varepsilon,\qquad \dot{\hat d}=l_2\varepsilon$$


$$s^2+l_1s+l_2=(s+\omega)^2\quad\Rightarrow\quad l_1=2\omega,\quad l_2=\omega^2$$


ω = π rad/s için l_1 = 6.283185307180 ve l_2 = 9.869604401089’dur. İki gözlemci hata kutbu -ω’da seçilir. Hız artığı hem hız kestirimine hem bozucu durumuna enjekte edilir. Bu raporda LESO, tam bir ADRC denetleyicisinin yerine geçmez; mevcut PI’ye kestirim sağlayan ek katmandır.



## 7.3 Bu örnekte beklenen davranış


Yerel olarak sabit bozucu varsayımı, sabit yük bölümleri için doğal bir başlangıçtır. Hızlı yük değişimleri ve sensör gecikmesi kestirimin gerisinde kalabilir. Kazanç büyüdükçe gürültü ve başlangıç geçişlerine duyarlılık artabilir. Kaydedilmiş deneyde LESO, DOB’a çok yakın başarım verir; daha basit nominal model kullanması tek başına daha iyi hata metriği getirmemiştir.



# 8. UDE: belirsizlik ve bozucu kestiricisi



## 8.1 Artığı süzme ilkesi


Zhong ve Rees’in UDE yaklaşımı, model denklemiyle hesaplanan belirsizlik ve bozucu artığının uygun bir süzgeçten geçirilmesine dayanır [5]. Buradaki normalize modelde ideal artık d = dr/dt - v’dir. Ham türev doğrudan alınırsa ölçüm gürültüsü büyüyebilir; bu yüzden türev ve süzme birlikte gerçekleştirilebilir bir aktarım olarak düzenlenir.


$$\hat d(s)=F(s)[sr(s)-v(s)],\qquad F(s)=\dfrac{\omega}{s+\omega}$$


$$\dfrac{\omega s}{s+\omega}=\omega-\dfrac{\omega^2}{s+\omega}$$



## 8.2 Tek durumlu gerçekleştirim


$$\dot z=-\omega z-\omega^2r-\omega v,\qquad \hat d=z+\omega r$$


ω = π rad/s ve ω² = 9.869604401089’dur. Tek z durumu, iki düşük geçiren bileşeni bir arada tutar. Çıkışta mevcut hızın doğrudan katkısı bulunur; yakıtın anlık doğrudan katkısı yoktur. Böylece ham sayısal türev bloğu olmadan filtrelenmiş artık elde edilir.


Bu gerçekleştirim, UDE’nin süzülmüş artık ilkesinin ortak PI arayüzüne uyarlanmasıdır; kaynak makaledeki denetleyicinin tüm yapısı kopyalanmış değildir. İdeal artık kestiriminin geçerliliği, bozucu içeriğinin seçilen filtre bandında bulunmasına bağlıdır. Ayrıca hızdan kestirime aktarım yüksek frekansta ω’ya yaklaşır; gürültü kazancı sonludur ama sıfır değildir.


Laplace aktarımı sıfır-durum ifadesidir. İlk normalize hız sıfır olmayabilir; z(0)=0 seçimi başlangıç geçişi üretir. Bu geçiş deney hazırlığında ele alınmıştır, genel bir sıçramasız başlatma garantisi değildir.



## 8.3 Sonuçların yönteme bağlanması


UDE her iki hızda en düşük tepe hız hatasını vermiştir. Bir temel durum gerektirmesi gömülü gerçekleştirim açısından çekicidir. Buna karşılık 9500 rpm hızlı rampasında DOB daha kısa toparlanma sağlar. Düşük tepe, hızlı toparlanma ve gürültü dayanıklılığı farklı hedeflerdir; bu gürültüsüz sonuçlardan sonuncusu çıkarılamaz.



# 9. GPIO: bozucu eğimini de kestirmek



## 9.1 Genişletilmiş durumun bir adım ötesi


GPIO, toplam bozucuyu ve gerekirse zamana göre türevlerini durum vektörüne ekleyen genelleştirilmiş gözlemci ailesidir. Sira-Ramírez’in senkron generatör çalışması, doğrusal olmayan etkilerin genişletilmiş doğrusal gözlemciyle kestirilmesi için bu raporun kaynaklarından biridir [6]. Burada kullanılan yapı, bozucunun yerel doğrusal değişimini temsil eden düşük mertebeli bir uyarlamadır.


$$\dot r=v+d,\qquad \dot d=h,\qquad \dot h\simeq0$$


LESO’nun yerel sabit bozucu varsayımı yerine, GPIO kısa bir zaman aralığında yaklaşık sabit eğim varsayar. Şaft gücü rampası bu tercihi motive eder. Bununla birlikte eşdeğer yakıt bozucusu, mekanik güç rampasıyla tam olarak aynı biçimde değişmek zorunda değildir; yakıt-hız dinamiği ve sensör de bu artığın içindedir.



## 9.2 Üç durumlu gözlemci


$$\dot{\hat r}=v+\hat d+l_1\varepsilon,\qquad \dot{\hat d}=\hat h+l_2\varepsilon,\qquad \dot{\hat h}=l_3\varepsilon$$


$$s^3+l_1s^2+l_2s+l_3=(s+\omega)^3$$


$$l_1=3\omega=9.424777960769,\quad l_2=3\omega^2=29.608813203268,\quad l_3=\omega^3=31.006276680300$$


Burada ε = r - r̂’dir. Üç tekrarlı kutup -π rad/s’de seçilir. İlave eğim durumu rampalı artıkta gecikmeyi azaltmayı amaçlar; daha fazla durum ve daha yüksek hata enjeksiyonu getirir. Rampa köşelerinde eğim süreksizleştiğinden yerel polinom varsayımı o anlarda bozulur.



## 9.3 Sonuçların yorumu


GPIO iki hızda da en düşük RMSE’yi verir. 9000 rpm hızlı ve orta süreli olaylarda ±1 rpm bandına en çabuk toparlanır. 9500 rpm’de bu üstünlük kaybolur ve telafi sinyali değerlendirme süresinin %2.133’ünde sınıra ulaşır. Sınırlamanın etkisi olası bir açıklamadır; neden-sonuç bağı ayrı bir deneyle yalıtılmamıştır.



# 10. Ayrık zamanlı temel blok gerçekleştirimleri



## 10.1 Sıfırıncı mertebeden tutucu ile ayrıklaştırma


$$\dot x=A_ox+B_ow,\quad \hat d=C_ox+D_ow,\qquad w=[r\;v]^{\mathsf{T}}$$


$$A_d=e^{A_oT_s},\qquad B_d=\int_0^{T_s}e^{A_o\tau}B_o\,d\tau$$


$$\hat d[k]=C_ox[k]+D_ow[k],\qquad x[k+1]=A_dx[k]+B_dw[k]$$


A_d ve B_d, genişletilmiş [A_o B_o; 0 0] matrisinin T_s ile çarpımının üstelinden birlikte hesaplanır. Bu, girişlerin örnek aralığında sabit tutulduğu doğrusal gözlemci için tam ayrıklaştırmadır. Sürekli değişen gerçek tesisin tam ayrık modeli olduğu iddia edilmez. Tüm başlangıç durumları sıfırdır.


Yöntem | Durumlar | C_o | D_o

LESO | [r̂, d̂] | [0, 1] | [0, 0]

UDE | z | [1] | [π, 0]

GPIO | [r̂, d̂, ĥ] | [0, 1, 0] | [0, 0]

ω = π için tek kutbun zaman sabiti 1/ω = 0.318309886184 s, ayrık kutup α = 0.953969203212’dir. Tek kutbun zaman sabiti, gözlemcinin veya kapalı çevrimin yerleşme süresi değildir. Aşağıdaki matrisler gösterim için yuvarlanır; kaynak JSON tam duyarlığı korur.



## 10.2 LESO sayısal matrisleri


A_d = [[0.9090144636031179, 0.01430953804817282], [-0.14122947969780208, 0.9989239428199246]]


B_d = [[0.0909855363968821, 0.01430953804817282], [0.14122947969780208, -0.0010760571800753882]]



# 10.3 UDE ve GPIO sayısal matrisleri



## UDE: bir durum


A_d = [[0.9539692032115213]]


B_d = [[-0.1446100130295695, -0.04603079678847873]]


$$\hat d[k]=z[k]+3.141592653590\,r[k]$$



## GPIO: üç durum


A_d = [[0.8651189450924479, 0.013972377501109792, 0.00010732153536129612], [-0.41703315665507235, 0.9968055006244576, 0.014983859142298868], [-0.4332314026810064, -0.0033276412191669278, 0.9999831639176581]]


B_d = [[0.13488105490755198, 0.013972377501109792], [0.41703315665507235, -0.0031944993755424187], [0.4332314026810064, -0.0033276412191669278]]



## 10.4 Bloklara eşleme


Unit Delay, x[k] durumunu saklar. Matris Gain blokları A_d x[k], B_d w[k] ve C_o x[k] çarpımlarını; Sum blokları toplamları gerçekleştirir. UDE’nin doğrudan hız katkısı ayrı bir Gain koludur. D_o’nun yakıt katsayısı sıfır olduğu için gereksiz doğrudan yakıt bağlantısı kurulmaz; böylece yapay cebirsel döngü oluşmaz.


Matrislerin hesaplandığı sürekli A_o ve B_o değerleri de tam duyarlıklı parametre dosyasında saklanır. Bu matrisler Bölüm 7-9 denklemlerinin doğrudan katsayılarıdır; ayrıklaştırmadan sonra yeniden kutup ayarı uygulanmaz.



# 11. Denge artığı ve nedensel işlem sırası



## 11.1 9500 rpm’de neden sıfır olmayan artık var?


İç ofsetler iki hızda da N_0 = 9000 rpm ve u_0 = 0.981086914682 lbm/s olarak kalır. 9500 rpm yüksüz dengede gerçek yakıt 1.849471360248 lbm/s’dir. Normalize model sabit hızda sıfır türev verdiğinden şu denge oluşur:


$$v_{\rm denge}=1.849471360248-0.981086914682=0.868384445565$$


$$0=\dot r=v_{\rm denge}+d_{\rm denge}\quad\Rightarrow\quad d_{\rm denge}=-0.868384445565\ \mathrm{lbm/s}$$


Bu sabit artık dış yükün kanıtı değildir; seçilen ofset ve yaklaşık modelin sonucudur. Denge belleği mutlak 30 saniyeye kadar seçilen ham kestirimi izler, ardından son değeri tutar. Telafide bu değer çıkarılır. Aynı mantık DOB’a da uygulanır. Sabit yanlılığın kaldırılması, giriş kazancını veya nominal modeli yeni hızda yeniden tanılamaz. Bu 30 s kilit, senaryoya özgü hazırlık protokolüdür; genel saha başlatma algoritması değildir (bölüm 27).



## 11.2 Her örnekte yürütme sırası


Adım | İşlem

1. Oku | Sensör hızı N_s ve önceki gözlemci durumu x[k] alınır.

2. Kestir | r[k] hesaplanır; C_o x[k] + D_o[0] r[k] oluşturulur.

3. Düzelt | Denge artığı çıkarılır; 0.25 kazanç, ±0.15 sınırı ve etkinleştirme uygulanır.

4. Yakıtı sınırla | Telafi PI’den çıkarılır; sonuç 0.2-4 lbm/s aralığına alınır.

5. Durumu güncelle | v[k] = u[k] - u_0 ile A_d x[k] + B_d w[k] hesaplanır.

6. İlerle ve kaydet | Tesis ilerletilir; hız, güç, çözüm yakınsaması ve gözlemci sinyalleri kaydedilir.

Kestirim çıkışı durum güncellemesinden önce hesaplanır. Bu sıra, uygulanmış sınırlı yakıtın aynı örnek sonundaki durum güncellemesinde kullanılmasını sağlar. Sayısal tekrar denetimi bu gerçekleştirimi doğrular; fiziksel bozucunun model hatasından ayrı ölçüldüğünü doğrulamaz.



# 12. İki hızdaki nicel sonuçlar


Her koşu 60 s hazırlık ve 90 s değerlendirmeden oluşur; toplam 150 s boyunca 10001 örnek vardır. 9000 rpm verileri ilk karşılaştırmadan korunmuştur. 9500 rpm deneyi aynı denetleyici ve rampa ayarlarıyla yapılmıştır. %10 yük, mutlak güç olarak 9500 rpm’de %62.528 daha büyüktür; hız ile yük genliği etkileri birbirinden yalıtılmamıştır.


$$e[k]=N[k]-N_{\rm istek},\quad {\rm RMSE}=\sqrt{\dfrac{1}{M}\sum_{k=1}^{M}e[k]^2},\quad e_{\max}=\max_k|e[k]|$$


$${\rm IAE}=T_s\sum_{k=1}^{M}|e[k]|$$


Hız | Yöntem | RMSE (rpm) | Tepe (rpm) | PI’ye göre RMSE azalması

9000 | PI | 1.193 | 10.677 | %0.00

9000 | DOB | 1.038 | 10.351 | %13.02

9000 | LESO | 1.039 | 10.349 | %12.90

9000 | UDE | 0.969 | 9.377 | %18.75

9000 | GPIO | 0.951 | 9.866 | %20.30

9500 | PI | 2.125 | 18.642 | %0.00

9500 | DOB | 1.850 | 18.147 | %12.94

9500 | LESO | 1.853 | 18.155 | %12.82

9500 | UDE | 1.730 | 16.574 | %18.59

9500 | GPIO | 1.698 | 17.393 | %20.10

<b>GPIO iki hızda en düşük RMSE’yi, UDE iki hızda en düşük tepe hatayı verir.</b> LESO, DOB’a çok yakındır. RMSE ortalama düzenleme başarımını, tepe en büyük sapmayı, IAE birikimli mutlak hatayı ölçer. Hiçbiri tek başına toparlanma hızını temsil etmez.


On koşunun tamamı sayısal geçerlilik denetimini geçer; yakıt sınırına ulaşan yoktur. 9500 rpm GPIO telafisi zamanın %2.133’ünde sınırlanır; diğer koşullarda telafi sınırı etkin değildir. Pozitif kompresör marjı tek başına doğrulanmış bir fiziksel işletim zarfı anlamına gelmez.



# 13. Genel zaman yanıtları: 9000 rpm


<i>Şekil 1. Gerçek hız, hız hatası, sınırlandırılmış yakıt ve şafttan çekilen güç. Zaman hazırlık sonrasından başlar. Beş denetleyici aynı mekanik yük profilini görür.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/genel_9000.png)


# 13. Genel zaman yanıtları: 9500 rpm


<i>Şekil 2. Gerçek hız, hız hatası, sınırlandırılmış yakıt ve şafttan çekilen güç. Zaman hazırlık sonrasından başlar. Beş denetleyici aynı mekanik yük profilini görür.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/genel_9500.png)


# 14. Bozucu bastırma yakın görünümleri: 9000 rpm


<i>Şekil 3. Altı rampa geçişi. Gri bölge rampa süresini, yeşil bölge ±1 rpm bandını gösterir. Yatay eksen ilgili rampa başlangıcına göredir.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/yakin_9000.png)

9000 rpm’de GPIO hızlı ve orta süreli olaylarda ±1 rpm bandına en kısa toparlanmayı sağlar. Daha dar ±0.5 rpm bandında DOB öne çıkar (bölüm 25-26). UDE hızlı rampanın ilk tepesini daha güçlü sınırlar. 3.00 s rampalarda gözlemci ekleri arasındaki toparlanma farkı en çok bir örnektir; bu fark tek başına seçim gerekçesi olmamalıdır.



# 14. Bozucu bastırma yakın görünümleri: 9500 rpm


<i>Şekil 4. Altı rampa geçişi. Gri bölge rampa süresini, yeşil bölge ±1 rpm bandını gösterir. Yatay eksen ilgili rampa başlangıcına göredir.</i>


![](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Turkce_Gozlemci_Makale/yakin_9500.png)

9500 rpm’de GPIO tüm deney RMSE’sinde önde kalır; ancak toparlanma üstünlüğünü korumaz. ±1 rpm bandında DOB altı olayda da en hızlı veya eşit en hızlıdır. ±2 rpm bandında sıralama değişir (bölüm 25-26). UDE en düşük tepeyi korur. Daha büyük yük ve değişen çalışma noktası altında farklı ölçütlerin sıralaması ayrışır.



# 15.1 Rampa bitiminden sonra toparlanma


Toparlanma, ±1 rpm bandı dışındaki son örnekten sonraki ilk uygun örnektir; sonraki rampaya kadar bandın içinde kalma ve en az 0.5 s doğrulama süresi aranır. Rampa sonrası süre, başlangıca göre süreden rampa süresinin çıkarılıp sıfırla aşağıdan sınırlandırılmasıdır. Tablodaki tüm değerler saniyedir; çözünürlük 15 ms’dir. Bu, yüzdeye dayalı yerleşme süresi değildir.



## 0.30 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 1.050 | 1.350 | 1.080 | 1.365

DOB | 0.705 | 0.855 | 0.735 | 0.870

LESO | 0.720 | 0.885 | 0.750 | 0.900

UDE | 0.780 | 0.990 | 0.795 | 1.005

GPIO | 0.615 | 0.990 | 0.630 | 0.870


## 1.50 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 0.630 | 0.945 | 0.645 | 0.930

DOB | 0.345 | 0.540 | 0.360 | 0.525

LESO | 0.345 | 0.555 | 0.375 | 0.540

UDE | 0.420 | 0.630 | 0.420 | 0.615

GPIO | 0.285 | 0.645 | 0.300 | 0.570


## 3.00 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 0.315 | 0.645 | 0.315 | 0.600

DOB | 0.165 | 0.330 | 0.150 | 0.285

LESO | 0.165 | 0.330 | 0.150 | 0.285

UDE | 0.165 | 0.390 | 0.150 | 0.360

GPIO | 0.150 | 0.330 | 0.150 | 0.315


# 15.2 Rampa başlangıcından itibaren toparlanma


Toparlanma, ±1 rpm bandı dışındaki son örnekten sonraki ilk uygun örnektir; sonraki rampaya kadar bandın içinde kalma ve en az 0.5 s doğrulama süresi aranır. Rampa sonrası süre, başlangıca göre süreden rampa süresinin çıkarılıp sıfırla aşağıdan sınırlandırılmasıdır. Tablodaki tüm değerler saniyedir; çözünürlük 15 ms’dir. Bu, yüzdeye dayalı yerleşme süresi değildir.



## 0.30 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 1.350 | 1.650 | 1.380 | 1.665

DOB | 1.005 | 1.155 | 1.035 | 1.170

LESO | 1.020 | 1.185 | 1.050 | 1.200

UDE | 1.080 | 1.290 | 1.095 | 1.305

GPIO | 0.915 | 1.290 | 0.930 | 1.170


## 1.50 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 2.130 | 2.445 | 2.145 | 2.430

DOB | 1.845 | 2.040 | 1.860 | 2.025

LESO | 1.845 | 2.055 | 1.875 | 2.040

UDE | 1.920 | 2.130 | 1.920 | 2.115

GPIO | 1.785 | 2.145 | 1.800 | 2.070


## 3.00 s uygulama ve kaldırma rampaları


Yöntem | Uygulama
9000 rpm | Uygulama
9500 rpm | Kaldırma
9000 rpm | Kaldırma
9500 rpm

PI | 3.315 | 3.645 | 3.315 | 3.600

DOB | 3.165 | 3.330 | 3.150 | 3.285

LESO | 3.165 | 3.330 | 3.150 | 3.285

UDE | 3.165 | 3.390 | 3.150 | 3.360

GPIO | 3.150 | 3.330 | 3.150 | 3.315


# 16. GZFT: PI ve modele dayalı DOB


GZFT, SWOT karşılığı olarak güçlü yönler, zayıf yönler, fırsatlar ve tehditleri gösterir. İlk iki boyut ölçülen kanıtları ve gerçekleştirim özelliklerini birleştirir. Fırsat ve tehditler geleceğe yönelik mühendislik değerlendirmeleridir; yeni deney sonucu değildir.



## 16.1 Temel PI


Boyut | Değerlendirme

Güçlü yönler | Basit ve izlenebilir geri besleme; bütün koşular geçerli. Tekrarlanabilir temel çizgi ve yedek denetim adayıdır.

Zayıf yönler | İki hızda da en büyük RMSE ve tepe sapması. Açık bozucu kestirimi ve ek anti-windup yoktur.

Fırsatlar | Yedek olarak korunabilir; karmaşıklık artırılmadan önce anti-windup ve kısıt yönetimi eklenebilir.

Tehditler | Kazanç değişimi, büyüyen yük ve yakıt doyumu bastırmayı bozabilir. Bu doyumsuz koşular integral yığılmasını sınamamıştır.


## 16.2 PI + tanılanmış model DOB


Boyut | Değerlendirme

Güçlü yönler | Daha ayrıntılı seyrek ARX modelini ve sensörlü nedensel tersi kullanır. 9500 rpm’de ±1 rpm bandında altı olayın tümünde en kısa veya eşit toparlanma.

Zayıf yönler | Nominal model hazırlığı, denge düzeltmesi ve ters filtre gerektirir. RMSE, UDE ve GPIO’dan yüksektir.

Fırsatlar | 9500 rpm toparlanma hedefi baskınsa öncelikli adaydır. Çalışma noktasına bağlı modeller ve ayrı Q ayarı sınanabilir.

Tehditler | Ters model uyumsuzluğu, belirsiz gecikme ve aşırı bant genişliği dayanıklılığı azaltabilir. Filtre kararlılığı genel kapalı çevrim garantisi değildir.


# 17. GZFT: LESO ve UDE



## 17.1 PI + LESO


Boyut | Değerlendirme

Güçlü yönler | İki durumlu çekirdek ve basit kutup ayarı; tam tesis tersi gerektirmez. İki hızda DOB’a yakın başarım.

Zayıf yönler | Mevcut DOB’a göre tüm-deney RMSE üstünlüğü yoktur. Yaklaşık b_0 ve yerel sabit eşdeğer bozucu kabulüne dayanır.

Fırsatlar | Daha basit nominal model seçeneğidir. Yerel giriş kazancı bağımsız tanılanıp gürültü/gecikme sınırlarıyla ayarlanabilir.

Tehditler | Yüksek gözlemci kazancı, kazanç işareti hatası, sensör gecikmesi ve ihmal edilen hızlı dinamikler geçiş tepesini artırabilir.


## 17.2 PI + UDE


Boyut | Değerlendirme

Güçlü yönler | Tek durum, ham türev yok; iki hızda en küçük tepe hata. PI’ye göre yaklaşık %19 daha düşük RMSE.

Zayıf yönler | 9500 rpm hızlı rampasında DOB’dan yavaş toparlanır. Doğrudan hız katkısı yüksek frekansta sonlu gürültü kazancı taşır.

Fırsatlar | Düşük tepe ve küçük durum sayısı öncelikliyse gömülü uygulama adayıdır. Ölçüm gürültüsüyle ayrıca doğrulanmalıdır.

Tehditler | Nicemleme, hız gürültüsü, gecikme ve filtre-tesis bant uyumsuzluğu deterministik üstünlüğü azaltabilir.

UDE önerisi koşulludur: az durum ve düşük tepe, en kısa toparlanmayı ya da en yüksek gürültü dayanıklılığını garanti etmez.



# 18. GZFT: GPIO ve gereksinime göre seçim



## 18.1 PI + rampalı bozucu GPIO


Boyut | Değerlendirme

Güçlü yönler | İki hızda en düşük RMSE; açık eğim durumu. 9000 rpm hızlı/orta olaylarda ±1 rpm bandına en iyi toparlanma.

Zayıf yönler | Üç durum; hızlı rampada tepe UDE’den büyüktür. 9500 rpm’de toparlanma liderliği kaybolur; telafi %2.133 süreyle sınırlanır.

Fırsatlar | Ortalama hata temel hedefse adaydır. Rampaların baskın olduğu bağımsız senaryolarda kısıtlı ve gürültülü ayar sınanabilir.

Tehditler | Eğim kestirimi, rampa köşeleri ve eşdeğer bozucunun doğrusal olmayan değişimi yerel rampa kabulünü zorlar. Kazanç artışı gürültüye duyarlılığı büyütebilir.


## 18.2 Hangi gereksinime hangi aday?


Seçim yalnız bu sabit ayarlar ve bu yük profilleri içindir. Toparlanma ifadeleri aksi belirtilmedikçe ±1 rpm bandına aittir. Hız, mutlak yük, etkin gözlemci bandı ve telafi sınırlaması etkileri ayrıştırılmamıştır; bant duyarlılığı bölüm 25-26’dadır.


Öncelik | Bu kanıtın desteklediği aday

Küçük gerçekleştirim ve düşük tepe | UDE; ardından gürültü ve gecikme doğrulaması.

Deneyde en düşük ortalama hata | GPIO; telafi sınırlaması gözetilerek.

9500 rpm’de ±1 rpm’ye hızlı toparlanma | Mevcut DOB; her olayda en hızlı veya eşit.

Basit modelle DOB benzeri yanıt | LESO; belirgin RMSE üstünlüğü olmadan.

0.30 s uygulama rampasında 9000 rpm rampa-sonrası süreleri GPIO için 0.615 s, DOB için 0.705 s’dir. 9500 rpm’de sırasıyla 0.990 s ve 0.855 s olur. Sınırlama bu değişime katkı yapabilir; ayrı bir neden-sonuç testi yapılmamıştır. Yalnız RMSE’ye bakarak denetleyici seçmek bu farkı gizler.



# 19. Doğrulama, sınırlar ve sonraki çalışmalar



## 19.1 Yapılan sayısal doğrulamalar


Her yörüngede sonlu sinyaller, pozitif yakıt ve pozitif kompresör marjı; en çok 10⁻⁹ akış artığı ve 200’den az çözücü yinelemesi aranmıştır. Mekanik yük zamanlaması ve yüksüz güç referansları eşleştirilmiştir. Moment dengesinden yeniden hesaplanan ivmenin kayda farkı 2.0 × 10⁻¹¹ rpm/s’den; yalnız LESO/UDE/GPIO’nun altı koşudaki bağımsız tekrar farkı 6.2 × 10⁻¹⁴ lbm/s’den küçüktür.


Bu kontroller benzetim ve denklem gerçekleştirimini doğrular. Kestirilen bozucunun gerçek dış yükten ayrı bir fiziksel ölçüm olduğunu göstermez. Her hızda tek deterministik senaryo vardır; sensör gürültüsü, parametre taraması, hedef işlem süresi ve güven aralığı yoktur. Aynı kutup parametresi etkin bantları eşitlemez. Farklı rampa süreleri farklı önceki yük geçmişleri ve tutma süreleri de içerir.



## 19.2 Gömülü uygulamaya giden yol


Aşama | Amaç

Bağımsız ayar ve ayrılmış doğrulama | Ayrı profilde ayar yap; görülmemiş senaryolarda tepe, RMSE, toparlanma ve yakıt hareketini ölç.

Dayanıklılık ve kısıtlar | Gürültü, nicemleme, sensör gecikmesi ve kazanç hatası ekle; yakıt, sıcaklık ve kompresör marjını değerlendir.

Hedef donanım | Anti-windup ve yedek mantığı ekle; işlem süresi, bellek ve sayısal duyarlığı ölç.

Bir sonraki karşılaştırmada aynı mutlak şaft gücü iki hızda uygulanarak hız ve yük genliği etkileri ayrılabilir. Observer frekansı, telafi kazancı ve sınırı bağımsız taranmalıdır. GPIO’nun sınırlandırmalı/sınırlandırmasız eşlenmiş deneyi toparlanma değişiminin nedenini inceleyebilir. Bu öneriler henüz yapılmış çalışma değildir.



# 19.3 Yeniden üretim ve genel değerlendirme


MATLAB R2018b, Simulink ve komşu T-MATS kütüphane/SimSetup dizinleri gereklidir. Model: <b>GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT.mdl</b>. 9500 rpm koşuları için <b>run_tmats_literature_comparison(9500)</b>, birleşik değerlendirme için <b>compare_observers_two_speeds.py</b> kullanılır. 9000 rpm veri grubu önceki doğrulanmış kayıttır.


Modeli yükledikten sonra <b>tmats_literature_setup(method,0.5,nominalRpm)</b> çağrılır; çünkü PreLoadFcn varsayılan olarak LESO’yu başlatır. method=1 mevcut DOB’u, aynı seçimde DOB.gain=0 temel PI’yi verir. Yöntem numaraları 2, 3 ve 4 sırasıyla LESO, UDE ve GPIO’yu seçer. Yeni koşu öncesinde ilgili yüksüz güç referansı hazır olmalıdır. Türkçe belge <b>build_observer_engineering_article.py</b> ile oluşturulur. Bu belge üretimi yalnızca kayıtlı verileri okur; benzetim çalıştırmaz.


Dosya / veri | İçerik

summary.json / .csv | Tüm deney başarım ölçütleri

events.json / .csv | Olay bazlı ölçütler

recovery_comparison.json / .csv | İki hız ve iki zaman tanımıyla toparlanma

verification.json | Moment ve gözlemci tekrar doğrulamaları

parameter_derivation.json | Tam duyarlıklı katsayılar ve matrisler

Türkçe rapor kaynakları | Türkçe grafikler, düzenlenebilir metin ve SHA-256 kayıtları


## Sonuç


Gözlemci ekleri bu deneylerde temel PI’yi iyileştirir; ancak bütün gereksinimlerde tek bir yöntem üstün değildir. UDE küçük gerçekleştirim ve tepe bastırma, GPIO ortalama hata, mevcut DOB ise sınanan 9500 rpm’de ±1 rpm bandına toparlanma açısından öne çıkar. V2’de farklı bantlarla yapılan yeniden değerlendirme, toparlanma sıralamasının gereksinime bağlı değiştiğini göstermiştir. Aran’ın çalışmaları, veriye dayalı nominal model artığını giriş eşdeğerinde kullanma fikrine sağlam bir yöntemsel bağ sunar; buradaki ARX-ters-filtre ve PI birleşimi projeye özgü bir uyarlamadır. Sonraki doğrulama, bu ayrımları ve gömülü sistem kısıtlarını koruyarak yapılmalıdır.


Bu belge, önceki İngilizce raporların kapsamını bir öğretici akışta korur. Hazırlık isteğinin 10 saniyede hedefe ulaşması, kaynak istek için geçerlidir; 9000 rpm’de hız isteği sınırlayıcısı uygulanan geçişi uzatır. Her iki deney değerlendirmeden önce yerleştiğinden bu açıklama veri veya ölçütleri değiştirmez.



# 20. Sayısal doğrulama ve sonuçların kapsamı


Bu bölüm, ana sonuçların yeniden hesabını ve yorumun geçerlilik sınırlarını bir araya getirir. V2’deki teknik denetimler korunmuştur. Amaç, okuyucunun bir yöntemin hangi ölçüte göre ve hangi koşullarda daha iyi olduğuna karar verebilmesidir.


Yeni tesis benzetimi ve denetleyici ayarı yapılmamıştır. Otuz ana skor (10 koşu × RMSE/tepe/IAE) ile 60 özgün olay toparlanması, ham CSV kayıtlarından yeniden hesaplanıp önceki değerlerle 10⁻⁹ toleransında eşleştirilmiştir. Değerlendirme son örneği skor hesabına dahil, olay penceresinin sağ ucu ise önceki kodla aynı biçimde hariçtir.


Kanıt türü | V2’de durum

Özgün hız sonuçları | RMSE, tepe ve ±1 rpm tabloları değişmedi.

Yeni analiz | ±0.5/1/2 rpm bant duyarlılığı; yakıt hareketi; nominal filtre kökleri.

Ana metin düzeltmesi | En hızlı ifadeleri bantla sınırlandı; arayüz, başlangıç ve tekrar kapsamı açıklandı.

Kanıtlanmayan | Gürbüz kapalı çevrim kararlılığı, gerçek valf fizibilitesi, termal zarf, hedef işlem süresi.


## Düzeltme sonrası ana sonuç


GPIO’nun RMSE ve UDE’nin tepe üstünlüğü kayıtlı deneylerde korunur. Toparlanma liderliği yalnız hızla değil, kabul bandıyla da değişir. ±0.5 rpm bandında DOB iki hızda bütün olaylarda en hızlı veya eşit en hızlıdır. Dolayısıyla yöntem seçimi için önce ürünün hata ve toparlanma gereksinimi tanımlanmalıdır.


Moment denetimi on koşuyu kapsar. 6.2 × 10⁻¹⁴ lbm/s gözlemci tekrar farkı yalnız LESO, UDE ve GPIO’nun iki hızdaki altı koşusuna aittir. DOB için aynı nitelikte bağımsız zaman alanı tekrar denetimi yapılmış gibi yorumlanmamalıdır.



# 21. Teorik açıklık: etkin bant ve kısmi telafi


Aşağıdaki aktarım fonksiyonları yalnız ideal normalize ṙ = v + d modeli, sıfır başlangıçlı gözlemci ve sürekli zaman denklemleri için türetilmiştir. Sensör, örnekleme, sınırlandırma ve doğrusal olmayan gaz türbini birlikte değerlendirildiğinde aynı bant değerleri doğrudan kullanılamaz.


$$F_{\rm LESO}(s)=\dfrac{\hat d}{d}=\dfrac{\omega^2}{(s+\omega)^2},\quad F_{\rm UDE}(s)=\dfrac{\omega}{s+\omega}$$


$$F_{\rm GPIO}(s)=\dfrac{3\omega^2s+\omega^3}{(s+\omega)^3}$$


Bu ifadeler gözlemci denklemlerinden r = (v+d)/s yerine konarak bulunur. GPIO payındaki sıfır, yalnız kutuplara bakılarak görülemeyen bir büyüklük tepesine neden olur. ω = π rad/s için DC kazancına göre ilk -3 dB geçişleri LESO 0.322 Hz, UDE 0.500 Hz, GPIO 0.821 Hz’dir. GPIO büyüklük tepesi yaklaşık 1.299’dur. Bu nedenle f_c = 0.5 Hz ayarı eşit kestirim bantları sağlamaz.



## Gerçek uygulamadaki %25 telafinin anlamı


$$P=P_n(1+\Delta),\quad u=u_c-gQ(P_n^{-1}y-u)$$


$$y=\dfrac{P}{1+gQ\Delta}u_c+\dfrac{P(1-gQ)}{1+gQ\Delta}d$$


Bu açıklamada y nominal modelle aynı çıkış değişkeni, d giriş bozucusu; denge çıkarılmış, etkinleştirme tamamlanmış ve doyum yoktur. g = 0.25 olduğundan Q ≈ 1 bölgesinde bile iç bozucu katsayısı 1-gQ sıfır olmaz. PI dış çevrimi u_c = K(r_ref-y) ile kapatılırsa ortak payda 1 + PK + gQΔ olur. Kararlılık, bu bütün yapıya ve belirsizliğe bağlıdır; yalnız Q kutuplarıyla ispatlanmaz.


Burada bir belirsizlik üst sınırı, Nyquist/gürbüzlük marjı veya doğrusal olmayan kararlılık teoremi sunulmamaktadır. Denklemler, ideal tam DOB ile sınanan kısmi telafi uygulamasını ayırmak içindir.



# 22. Nominal ters, katsayı düzeltmesi ve birimler


q = z⁻¹ tanımında katsayı dizisine roots uygulanması, polinom z’nin uygun kuvvetiyle çarpıldıktan sonraki z-düzlemi köklerini verir. Aşağıdaki büyüklükler q-düzlemi kökü olarak yorumlanmamalıdır. Dizinin sonundaki sıfır dolgu, z = 0 kökleri ekleyebilir; bu kökler birim çember dışı kararsızlık oluşturmaz.


Denetim | En büyük |z| / değer

A nominal kutupları | 0.977742089

C minimum-faz sıfırları | 0.952615717

Q tasarım kutbu | 0.953969203

Açılmış Q/P_n payda kökleri | 0.953969861

Nominal hız DC kazancı | 335.425155 rpm / (lbm/s)

Tekrarlı Q kutupları, açılmış polinomun sayısal kök hesabında yaklaşık 6.6 × 10⁻⁷ kadar ayrışabilir. Tüm ilgili kökler birim çember içindedir; gecikmeler Q ile karşılanmıştır. Bu sonuç nominal ters filtrenin uygulanabilirliğini destekler; tüm kapalı çevrimin sağlamlık kanıtı değildir.


B_eq düzeltmesi son katsayıyı yalnız %0.041692 değiştirir; fakat B_eq(1)=0 kısıtı sıfır frekans yapısını değiştirir. Küçük katsayı değişimi, bağımsız model doğrulaması yerine geçmez. b_0 bir-adımlı ARX katsayısından alınmıştır; gerçek sürekli-zaman yerel giriş Jacobian’ı olduğu doğrulanmamıştır. 9500 rpm’de güncelleme yapılmaz.


Büyüklük | Birim / açıklama

K_p | (lbm/s) / rpm

K_i | (lbm/s) / (rpm·s)

b_0 | (rpm/s) / (lbm/s)

r = (N_s-N_0)/b_0 | lbm; ṙ ve d birimi lbm/s

Toparlanma bandı | Mutlak rpm; ürün kabul şartı değil proje metriği


# 23. Mühendislik büyüklüğü ve birikimli hata


Aşağıdaki farklar pozitif olduğunda temel PI’ye göre iyileşme vardır. Yüzde tepe, tepe hatanın nominal hıza oranıdır; RMSE azalması yüzdesiyle karıştırılmamalıdır. Birkaç rpm kazanımın gerekli veya yeterli olduğuna karar vermek için sensör çözünürlüğü ve ürün şartı bilinmelidir.


Hız | Yöntem | Tepe / N<br/>(%) | Tepe kazancı<br/>(rpm) | RMSE kazancı<br/>(rpm) | IAE<br/>(rpm·s)

9000 | PI | 0.1186 | 0.000 | 0.000 | 36.7736

9000 | DOB | 0.1150 | 0.326 | 0.155 | 28.3409

9000 | LESO | 0.1150 | 0.328 | 0.154 | 28.6944

9000 | UDE | 0.1042 | 1.300 | 0.224 | 27.5872

9000 | GPIO | 0.1096 | 0.811 | 0.242 | 27.5774

9500 | PI | 0.1962 | 0.000 | 0.000 | 65.8633

9500 | DOB | 0.1910 | 0.494 | 0.275 | 50.7992

9500 | LESO | 0.1911 | 0.486 | 0.273 | 51.4286

9500 | UDE | 0.1745 | 2.068 | 0.395 | 49.4106

9500 | GPIO | 0.1831 | 1.248 | 0.427 | 49.3923

UDE ile PI arasındaki mutlak tepe farkı 9000 rpm’de 1.300 rpm, 9500 rpm’de 2.068 rpm’dir. GPIO’nun RMSE farkları 0.242 ve 0.427 rpm’dir. Bunlar belirli denetleyici ayarlarının bu profillerdeki sayısal kazançlarıdır; ürünün yeterlilik veya sertifikasyon göstergesi değildir.


UDE ile GPIO’nun IAE farkı çok küçüktür: yaklaşık 0.00985 ve 0.01825 rpm·s. Bu deterministik sıralama için istatistiksel veya bakım maliyeti açısından anlamlılık iddia edilmiyor. Tek bir metrikte küçük farklar yerine, gereksinim ve kontrol eforu birlikte değerlendirilmelidir.


Skorlar 60-150 s aralığında iki uç dahil 6001 örnekten hesaplanır. IAE, önceki kodla aynı T_sΣ|e| dikdörtgen toplamıdır; sürekli integralin tam değeri değildir. Toplam 10001 örnek, hazırlık dahil 150 saniyelik koşuya aittir.



# 24. Yakıt hareketi ve fiziksel kanıt sınırı


$${\rm TV}_u=\sum_{k=2}^{M}|u[k]-u[k-1]|,\qquad R_u=\max_k\dfrac{|u[k]-u[k-1]|}{T_s}$$


TV_u birimi lbm/s, R_u birimi lbm/s²’dir. TV yakıt tüketimi değil, örneklenmiş komut hareketinin toplamıdır. R_u sürekli-zaman tepe türevi veya uygulanmış valf hız sınırı değildir. Değerler aynı 6001 değerlendirme örneğinden çıkarılmıştır.


Hız | Yöntem | TV_u<br/>(lbm/s) | R_u<br/>(lbm/s²) | En az marj<br/>(%) | Telafi sınırı<br/>(%)

9000 | PI | 2.1157 | 1.4157 | 24.429 | 0.000

9000 | DOB | 2.1363 | 1.4357 | 24.322 | 0.000

9000 | LESO | 2.1426 | 1.4419 | 24.302 | 0.000

9000 | UDE | 2.1436 | 1.4742 | 24.389 | 0.000

9000 | GPIO | 2.1744 | 1.4848 | 24.161 | 0.000

9500 | PI | 3.7125 | 2.4316 | 16.669 | 0.000

9500 | DOB | 3.7628 | 2.4712 | 16.543 | 0.000

9500 | LESO | 3.7734 | 2.4812 | 16.522 | 0.000

9500 | UDE | 3.7796 | 2.5407 | 16.576 | 0.000

9500 | GPIO | 3.8453 | 2.5616 | 16.356 | 2.133

GPIO’nun TV değeri temel PI’ye göre 9000 rpm’de yaklaşık %2.77, 9500 rpm’de %3.58 fazladır. Minimum kompresör marjı da PI’den biraz düşüktür. Dolayısıyla daha düşük hız hatası, tüm yan ölçütlerde eşzamanlı iyileşme demek değildir. Bakım veya yakıt ekonomisi sonucu için uygun fiziksel model ve kabul sınırı gerekir.


On koşunun değerlendirme aralığında DOB_command ile Wf farkı tam sıfırdır. Bu, modelde komut-debi özdeşliğini doğrular; gerçek yakıt valfinin dinamiklerini doğrulamaz. Bu karşılaştırmanın CSV kayıtlarında sıcaklık kanalı ve termal kabul sınırı yoktur. Sayısal geçerlilik fiziksel işletim güvenliği ile eşdeğer değildir.



# 25. Toparlanma bandına duyarlılık


V1’de kullanılan algoritma aynen korunarak ±0.5, ±1 ve ±2 rpm bantları değerlendirildi. Her pencere rampa başlangıcından sonraki rampa başlangıcına kadardır; sağ uç hariçtir. Son bant dışı örnekten sonra bandın içinde kalma ve en az 0.5 s doğrulama koşulu aynıdır. İnterpolasyon yapılmaz; bütün zamanlar 15 ms çözünürlüklüdür.



## 9000 rpm: 0.30 s yük uygulamasından sonra


Yöntem | ±0.5 rpm (s) | ±1 rpm (s) | ±2 rpm (s)

PI | 1.380 | 1.050 | 0.735

DOB | 0.870 | 0.705 | 0.525

LESO | 0.900 | 0.720 | 0.540

UDE | 1.005 | 0.780 | 0.525

GPIO | 0.900 | 0.615 | 0.465


## 9500 rpm: 0.30 s yük uygulamasından sonra


Yöntem | ±0.5 rpm (s) | ±1 rpm (s) | ±2 rpm (s)

PI | 1.680 | 1.350 | 1.020

DOB | 0.990 | 0.855 | 0.690

LESO | 1.020 | 0.885 | 0.705

UDE | 1.230 | 0.990 | 0.750

GPIO | 1.320 | 0.990 | 0.645

9000 rpm hızlı uygulamasında ±1 rpm bandı GPIO’yu (0.615 s), ±0.5 rpm bandı DOB’u (0.870 s) öne çıkarır. 9500 rpm’de ±1 rpm DOB’u (0.855 s), ±2 rpm GPIO’yu (0.645 s) öne çıkarır. Bunlar aynı yörüngenin farklı gereksinimlerle okunmasıdır; yeni bir kontrol deneyi değildir.



# 26. Altı olayda eşik duyarlılığı özeti


Tablo, her hız ve bantta en küçük rampa-sonrası süreyi veren yöntemleri gösterir. “/” eşitliktir: aynı örneğe denk gelen süreler 10⁻⁷ s sayısal toleransla eşit kabul edilir. Bir örneklik farklar gerçek donanımda belirleyici üstünlük olarak yorumlanmamalıdır.



## 9000 rpm


Olay | ±0.5 rpm | ±1 rpm | ±2 rpm

0.30 s uyg. | DOB | GPIO | GPIO

0.30 s kald. | DOB | GPIO | GPIO

1.50 s uyg. | DOB | GPIO | GPIO

1.50 s kald. | DOB | GPIO | GPIO

3.00 s uyg. | DOB/LESO | GPIO | DOB/LESO/UDE/GPIO

3.00 s kald. | DOB | DOB/LESO/UDE/GPIO | DOB/LESO/UDE/GPIO


## 9500 rpm


Olay | ±0.5 rpm | ±1 rpm | ±2 rpm

0.30 s uyg. | DOB | DOB | GPIO

0.30 s kald. | DOB | DOB/GPIO | GPIO

1.50 s uyg. | DOB | DOB | GPIO

1.50 s kald. | DOB | DOB | GPIO

3.00 s uyg. | DOB/LESO | DOB/LESO/GPIO | GPIO

3.00 s kald. | DOB/LESO | DOB/LESO | DOB/LESO/UDE/GPIO

±0.5 rpm’de DOB her iki hızda altı olayın tamamında en hızlı veya eşit en hızlıdır. ±2 rpm’de GPIO 9500 rpm’nin ilk beş olayında en hızlıdır. Bu sonuç V1’in ±1 rpm sayısal tablosunu geçersiz kılmaz; “en hızlı yöntem” sonucunun bant belirtilmeden genellenemeyeceğini gösterir. Tüm 180 olay/bant değeri audit.json içinde saklanır.



# 27. Uygulamaya geçiş ve yeniden üretim kontrolü


Konu | Doğrulanan | Henüz doğrulanmayan

Sensör / eyleyici | 0.05 s gürültüsüz sensör; komut=debi | Gürültü, nicemleme, valf bant/hız sınırı, ölü bölge

Denge kabulü | 30 s kilit; hazırlık sonrası yerleşme | Yük altında etkinleşme, yeniden başlatma, hız değişiminde yeniden denge

Gömülü maliyet | UDE/LESO/GPIO: 1/2/3 çekirdek durum | Toplam bellek, tek duyarlık, hedef işlem süresi, SIL/PIL/HIL

Fiziksel kabul | Kayıtlı marj pozitif, yakıt doyumu yok | Sıcaklık sınırları, güvenli işletim zarfı, ürün kabul şartları

Saha adayı denge mantığı; düşük hız türevi, küçük hata, kararlı yakıt ve asgari bekleme süresiyle koşullu denge kabulünü içermelidir. Hata halinde PI’ye geri dönüş ve yumuşak yeniden etkinleştirme değerlendirilebilir. Bu mantık mevcut modele eklenmiş veya sınanmış değildir.


Sabit A_d/B_d matrisleri çevrim dışında hazırlanabilir; çevrimde çarpım/toplam işlemleri kalır. Ancak trim belleği, doyum, etkinleştirme, sensör ve gözetim maliyeti de vardır. Temel Simulink blokları otomatik kod üretimi veya hedef zamanlama kanıtı sayılmaz. T_s = 15 ms yalnız model örnekleme süresidir.



## Yeniden üretim sırası


Yeni benzetimde önce yüksüz güç referansını hazırlayın; sonra modeli yükleyin ve kurulumu çağırın. method=1 mevcut DOB’u seçer; aynı seçimde DOB.gain=0 temel PI’yi verir. method=2/3/4, LESO/UDE/GPIO’dur. run_tmats_literature_comparison bu seçimi yapar. Komşu T-MATS kütüphanesi ve SimSetup bağımlılıkları korunur.


Yalnız kayıtlı veriyi denetlemek için audit_observer_v2.py, ardından build_observer_engineering_article.py çalıştırılır. Makale oluşturucusu önceki betikleri salt kaynak olarak kullanır ve çıktıları ayrı makale klasörüne yönlendirir. V1 PDF ve betik değişmez. Denetim girdilerinin SHA-256 kayıtları audit.json; rapor kaynakları ve PDF’lerin kayıtları makale source_sha256.json dosyasındadır.


Bu makale, sayısal sonuçları yöntem türetimi ve mühendislik yorumu ile birlikte sunar. Yeni bir uygulama için önce kabul bandı ve fiziksel sınırlar tanımlanmalı, ardından eşlenmiş deneylerle aday yöntem doğrulanmalıdır.



# Kaynakça


<b>[1]</b> V. Aran, <i>Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models</i>, doktora tezi, Sabancı Üniversitesi, Temmuz 2019. Özellikle bölüm 4.1-4.2, basılı s. 42-47; bölüm 6.1, s. 60-64; bölüm 7.6. Türkçe adı: Veriye Dayalı Bozucu Gözlemcileri ve GPR Modelleri Kullanarak Esnek ve Gürbüz Dizel Motor Havayolu Kontrolü. <link href="https://research.sabanciuniv.edu/39260/2/10279446_VolkanAran.pdf" color="#087e8b">Kaynağa erişim</link>


<b>[2]</b> V. Aran ve M. Ünel, “Data driven disturbance observer design and control for diesel engine airpath,” 11th Asian Control Conference, 2017. DOI: 10.1109/ASCC.2017.8287586. <link href="https://research.sabanciuniv.edu/35812/" color="#087e8b">Kaynağa erişim</link>


<b>[3]</b> Z. Gao, “Scaling and bandwidth-parameterization based controller tuning,” American Control Conference, cilt 6, s. 4989-4996, 2003. DOI: 10.1109/ACC.2003.1242516. <link href="https://engagedscholarship.csuohio.edu/enece_facpub/528/" color="#087e8b">Kaynağa erişim</link>


<b>[4]</b> G. Herbst, “A simulative study on active disturbance rejection control (ADRC) as a control tool for practitioners,” Electronics, 2(3), s. 246-279, 2013. DOI: 10.3390/electronics2030246. Bağlantı yazarın arXiv sürümüdür. <link href="https://arxiv.org/html/1908.04596" color="#087e8b">Kaynağa erişim</link>


<b>[5]</b> Q.-C. Zhong ve D. Rees, “Control of uncertain LTI systems based on an uncertainty and disturbance estimator,” Journal of Dynamic Systems, Measurement, and Control, 126(4), s. 905-910, 2004. DOI: 10.1115/1.1850529. <link href="https://doi.org/10.1115/1.1850529" color="#087e8b">Kaynağa erişim</link>


<b>[6]</b> H. Sira-Ramírez, “Robust linear output feedback control of a synchronous generator,” American Control Conference, s. 3728-3733, 2011. DOI: 10.1109/ACC.2011.5990756. <link href="https://skoge.folk.ntnu.no/prost/proceedings/acc11/data/papers/0048.pdf" color="#087e8b">Kaynağa erişim</link>


<b>[7]</b> J. W. Chapman, T. M. Lavelle, R. D. May, J. S. Litt ve T.-H. Guo, <i>Toolbox for the Modeling and Analysis of Thermodynamic Systems (T-MATS) User’s Guide</i>, NASA/TM-2014-216638, Ocak 2014. Özellikle bölüm 1, 7.3 ve 7.3.2. <link href="https://ntrs.nasa.gov/citations/20140012486" color="#087e8b">Kaynağa erişim</link>


Tarihsel DOB atfı: K. Ohishi, K. Ohnishi ve K. Miyachi, “Torque-speed regulation of DC motor based on load torque estimation,” IPEC-Tokyo, s. 1209-1216, 1983; burada Aran tezinin [67] numaralı kaynağı üzerinden anılmıştır. Literatür ilkeleri açıklamak için kullanılmıştır; bu rapordaki sayısal sonuçlar yayınlardan alınmamıştır.



# Kaynak ve veri izlenebilirliği


Bu Türkçe sürümün ana kaynağı 20 sayfalık <i>PI Disturbance-Rejection Augmentations for a Dynamic Gas-Turbine Model</i> kapsamlı öğretici raporudur. Bu rapor daha önce 12 sayfalık <i>Comparison of PI Disturbance-Rejection Augmentations for a Dynamic Gas-Turbine Model</i> ile 15 sayfalık iki-hız raporunu birleştirmiştir. Önceki PDF’ler ve ham veriler korunur.


Türkçeleştirme yalnızca açıklamaları kapsamaz: grafik eksenleri, şekil açıklamaları, tablo başlıkları ve GZFT metinleri de Türkçedir. Kaynak eser adları, standart kısaltmalar, birimler ve yazılım dosya adları bilimsel izlenebilirlik için özgün biçimdedir. Formüller numaralı matematik dizgisiyle, matrisler hizalı ve köşeli parantezli gösterilmiştir.


Sabit veri grupları:<br/>9000 rpm: literature_observers_9000rpm_10pct_20260912_211600_355<br/>9500 rpm: literature_observers_9500rpm_10pct_20260912_213607_364<br/>Birleşik değerlendirme: results/Observer_9000_9500_Comparison


Yerel tez kopyası tmp/dob/Volkan_Aran_PhD_2019.pdf üzerinden okunmuştur. Tezin PDF sayfa 58-63 bölümü, basılı sayfa 42-47’ye karşılık gelir. Yöntem açıklamaları özgün cümlelerin uzun çevirileri yerine denklemler ve bağlamın bu uygulamaya yönelik açıklamasıdır. Tezdeki algoritma ile test edilmiş gaz türbini DOB’u özellikle ayrılmıştır.


Belge durumu: bilimsel makale biçiminde proje öğreticisi ve teknik kayıt; hakemli yayın değildir. Referanslardaki tam denetleyicilerin veya kararlılık garantilerinin bu projede aynen yeniden üretildiği iddia edilmez. Açıklamalar, sabit ayarlı ve gürültüsüz benzetimlerin kapsamıyla sınırlıdır.



## Kaynak bütünlüğü


Eşlik eden SHA-256 kaydı; bu PDF’yi, oluşturma betiğini, önceki kapsamlı PDF’yi, tam parametre dosyasını ve sonuç tablolarını tanımlar. Türkçe grafikler özgün sayısal örneklerden yeniden çizilmiştir. Düzenlenebilir metin, denklemlerin LaTeX gösterimleriyle birlikte aynı sonuç klasöründe tutulur.
