from django.urls import path
from . import views

urlpatterns = [
    # HIZI NDIO LINK ZA KUINGIA NA KUTOKA
    path('ingia/', views.ingia, name='ingia'),
    path('toka/', views.toka, name='toka'),
    path('', views.ukurasa_wa_mwanzo, name='mwanzo'), 
    
    # Madarasa na Wanafunzi
    path('wanafunzi/', views.orodha_wanafunzi, name='orodha_wanafunzi'),
    path('wanafunzi/sajili/', views.sajili_mwanafunzi, name='sajili_mwanafunzi'),
    path('wanafunzi/hariri/<int:id>/', views.hariri_mwanafunzi, name='hariri_mwanafunzi'),
    path('wanafunzi/hifadhi/<int:mwanafunzi_id>/', views.hifadhi_mwanafunzi, name='hifadhi_mwanafunzi'),
    path('wanafunzi/rudisha/<int:mwanafunzi_id>/', views.rudisha_mwanafunzi, name='rudisha_mwanafunzi'),
    path('walimu/', views.orodha_walimu, name='orodha_walimu'),
    path('walimu/ongeza/', views.ongeza_mwalimu, name='ongeza_mwalimu'),
    path('walimu/hariri/<int:mwalimu_id>/', views.hariri_mwalimu, name='hariri_mwalimu'),
    path('madarasa/', views.orodha_madarasa, name='orodha_madarasa'),
    path('madarasa/ongeza/', views.ongeza_darasa, name='ongeza_darasa'),
    path('madarasa/hariri/<int:darasa_id>/', views.hariri_darasa, name='hariri_darasa'),
    path('madarasa/futa/<int:darasa_id>/', views.futa_darasa, name='futa_darasa'),
    path('madarasa/<int:darasa_id>/', views.wanafunzi_darasa, name='wanafunzi_darasa'),
    path('aina-malipo/', views.orodha_aina_malipo, name='orodha_aina_malipo'),
    path('aina-malipo/ongeza/', views.ongeza_aina_malipo, name='ongeza_aina_malipo'),
    path('aina-malipo/hariri/<int:aina_id>/', views.hariri_aina_malipo, name='hariri_aina_malipo'),
    path('aina-malipo/futa/<int:aina_id>/', views.futa_aina_malipo, name='futa_aina_malipo'),
    path('mwanafunzi/profile/<int:mwanafunzi_id>/', views.mwanafunzi_profile, name='mwanafunzi_profile'),
    
    # Mahudhurio
    path('madarasa/<int:darasa_id>/mahudhurio/', views.mahudhurio_darasa, name='mahudhurio_darasa'),
    path('hifdhu/mahudhurio/<int:somo_id>/', views.chukua_mahudhurio_hifdhu, name='chukua_mahudhurio_hifdhu'),
    
    # ==== NJIA MPYA ZENYE AKILI KWA AJILI YA SABAQ NA RIPOTI ====
    path('rekodi_sabaq/<int:mwanafunzi_id>/<str:aina>/', views.rekodi_sabaq, name='rekodi_sabaq'),
    path('ripoti/<int:mwanafunzi_id>/<str:aina>/', views.ripoti_mwanafunzi, name='ripoti_mwanafunzi'),
    path(
        'masomo/<int:somo_id>/maendeleo/',
        views.wanafunzi_maendeleo_mchana,
        name='wanafunzi_maendeleo_mchana',
    ),
    path(
        'maendeleo/<int:mwanafunzi_id>/<int:somo_id>/rekodi/',
        views.rekodi_maendeleo_mchana,
        name='rekodi_maendeleo_mchana',
    ),
    path(
        'maendeleo/<int:mwanafunzi_id>/ripoti/',
        views.ripoti_maendeleo_mchana,
        name='ripoti_maendeleo_mchana',
    ),
    
    # Njia za PDFs (Zimesasishwa kubeba Kichujio cha Muda)
    path('pdf/mahudhurio/<int:mwanafunzi_id>/<str:aina>/<str:muda>/', views.pakua_pdf_mahudhurio, name='pakua_pdf_mahudhurio'),
    path('pdf/sabaq/<int:mwanafunzi_id>/<str:aina>/<str:muda>/', views.pakua_pdf_sabaq, name='pakua_pdf_sabaq'),
    
    # Masomo Mengine na Watoro
    path('masomo/', views.orodha_masomo, name='orodha_masomo'),
    path('masomo/<int:somo_id>/', views.somo_detail, name='somo_detail'),
    path('somo/<int:somo_id>/nyenzo/pakia/', views.pakia_nyenzo, name='pakia_nyenzo'),
    path('somo/<int:somo_id>/mtihani/ongeza/', views.ongeza_mtihani, name='ongeza_mtihani'),
    
    # ==== NJIA ZA MITIHANI NA MAKSI ====
    path('mtihani/<int:mtihani_id>/maksi/', views.weka_maksi, name='weka_maksi'),
    path('mtihani/<int:mtihani_id>/matokeo/', views.tazama_matokeo, name='tazama_matokeo'),
    path('mtihani/<int:mtihani_id>/matokeo/pdf/', views.pakua_pdf_matokeo, name='pakua_pdf_matokeo'),

    # ==== MSETO WA MITIHANI NA RIPOTI YA JUMLA ====
    path('madarasa/<int:darasa_id>/mseto/', views.mseto_mitihani_darasa, name='mseto_mitihani_darasa'),
    path('madarasa/<int:darasa_id>/mseto/<int:mseto_id>/ripoti/', views.ripoti_jumla, name='ripoti_jumla'),
    path('madarasa/<int:darasa_id>/mseto/<int:mseto_id>/ripoti/pdf/', views.pakua_pdf_matokeo_jumla, name='pakua_pdf_matokeo_jumla'),
    path('madarasa/<int:darasa_id>/mseto/<int:mseto_id>/ripoti/csv/', views.pakua_csv_matokeo_jumla, name='pakua_csv_matokeo_jumla'),
    path('mwaka/', views.ukurasa_mwaka_masomo, name='mwaka_masomo'),
    path('hamisha-darasa/', views.hamisha_darasa, name='hamisha_darasa'),
    path('ukaguzi/', views.orodha_ukaguzi, name='orodha_ukaguzi'),
    path('mawasiliano/', views.orodha_mawasiliano, name='orodha_mawasiliano'),
    path('mawasiliano/whatsapp/', views.tuma_whatsapp, name='tuma_whatsapp'),
    path(
        'mawasiliano/<int:mwanafunzi_id>/',
        views.mwanafunzi_mawasiliano,
        name='mwanafunzi_mawasiliano',
    ),
    path(
        'mawasiliano/<int:mwanafunzi_id>/simu/',
        views.rekodi_simu_kutoka_profile,
        name='rekodi_simu_kutoka_profile',
    ),
    path(
        'mawasiliano/<int:mwanafunzi_id>/whatsapp/',
        views.fungua_whatsapp,
        name='fungua_whatsapp',
    ),
    
    path('hifdhu/kundi/<int:somo_id>/', views.wanafunzi_hifdhu, name='wanafunzi_hifdhu'),
    path('ripoti/watoro/', views.ripoti_watoro, name='ripoti_watoro'),
    
    # === NJIA ZA MALIPO ===
    path('malipo/', views.ukurasa_malipo, name='malipo'),
    path('malipo/weka/<int:mwanafunzi_id>/<int:aina_id>/', views.weka_malipo, name='weka_malipo'),
    # NJIA MPYA YA RISITI
    path('malipo/risiti/<int:malipo_id>/', views.pakua_risiti, name='pakua_risiti'),
]
