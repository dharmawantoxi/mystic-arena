extends RefCounted
## Explicit native portrait catalog for all remaining non-fallback heroes.

const KAEDRIN_PAINTER = preload("res://scripts/ui/hero_portrait_kaedrin.gd")
const KAELDRIS_PAINTER = preload("res://scripts/ui/hero_portrait_kaeldris.gd")
const KAELTHAR_PAINTER = preload("res://scripts/ui/hero_portrait_kaelthar.gd")
const KAELTHORN_PAINTER = preload("res://scripts/ui/hero_portrait_kaelthorn.gd")
const KAELTHYS_PAINTER = preload("res://scripts/ui/hero_portrait_kaelthys.gd")
const KAELVYRN_PAINTER = preload("res://scripts/ui/hero_portrait_kaelvyrn.gd")
const KAERINYA_PAINTER = preload("res://scripts/ui/hero_portrait_kaerinya.gd")
const KAERVOSTH_PAINTER = preload("res://scripts/ui/hero_portrait_kaervosth.gd")
const KAGETSUKA_PAINTER = preload("res://scripts/ui/hero_portrait_kagetsuka.gd")
const KAINEROTH_PAINTER = preload("res://scripts/ui/hero_portrait_kaineroth.gd")
const KAIRENJI_PAINTER = preload("res://scripts/ui/hero_portrait_kairenji.gd")
const KAITHROS_PAINTER = preload("res://scripts/ui/hero_portrait_kaithros.gd")
const KAIZOKU_RAIJIN_PAINTER = preload("res://scripts/ui/hero_portrait_kaizoku_raijin.gd")
const KAORUKEN_PAINTER = preload("res://scripts/ui/hero_portrait_kaoruken.gd")
const KARZHUL_PAINTER = preload("res://scripts/ui/hero_portrait_karzhul.gd")
const KASSADIN_PAINTER = preload("res://scripts/ui/hero_portrait_kassadin.gd")
const KAZUREN_PAINTER = preload("res://scripts/ui/hero_portrait_kazuren.gd")
const KAZURETH_PAINTER = preload("res://scripts/ui/hero_portrait_kazureth.gd")
const KENSHIRO_PAINTER = preload("res://scripts/ui/hero_portrait_kenshiro.gd")
const KHALROS_PAINTER = preload("res://scripts/ui/hero_portrait_khalros.gd")
const KHALZAREDH_PAINTER = preload("res://scripts/ui/hero_portrait_khalzaredh.gd")
const KHAZAN_PAINTER = preload("res://scripts/ui/hero_portrait_khazan.gd")
const KOROKAI_PAINTER = preload("res://scripts/ui/hero_portrait_korokai.gd")
const KROBELLUS_PAINTER = preload("res://scripts/ui/hero_portrait_krobellus.gd")
const KROGNARR_PAINTER = preload("res://scripts/ui/hero_portrait_krognarr.gd")
const KRYVOXAR_PAINTER = preload("res://scripts/ui/hero_portrait_kryvoxar.gd")
const KUROGARI_PAINTER = preload("res://scripts/ui/hero_portrait_kurogari.gd")
const KYRENZAI_PAINTER = preload("res://scripts/ui/hero_portrait_kyrenzai.gd")
const KYUMIRRA_PAINTER = preload("res://scripts/ui/hero_portrait_kyumirra.gd")
const LEORIC_PAINTER = preload("res://scripts/ui/hero_portrait_leoric.gd")
const LUMINAR_PAINTER = preload("res://scripts/ui/hero_portrait_luminar.gd")
const LYRENYA_PAINTER = preload("res://scripts/ui/hero_portrait_lyrenya.gd")
const LYRIENNE_PAINTER = preload("res://scripts/ui/hero_portrait_lyrienne.gd")
const LYSSARETHYS_PAINTER = preload("res://scripts/ui/hero_portrait_lyssarethys.gd")
const MALZARETH_PAINTER = preload("res://scripts/ui/hero_portrait_malzareth.gd")
const MALZEROTH_PAINTER = preload("res://scripts/ui/hero_portrait_malzeroth.gd")
const MOLGRAVAR_PAINTER = preload("res://scripts/ui/hero_portrait_molgravar.gd")
const MORKHAERA_PAINTER = preload("res://scripts/ui/hero_portrait_morkhaera.gd")
const MORKHELVIS_PAINTER = preload("res://scripts/ui/hero_portrait_morkhelvis.gd")
const MORTHYRAX_PAINTER = preload("res://scripts/ui/hero_portrait_morthyrax.gd")
const MORVAENTHIR_PAINTER = preload("res://scripts/ui/hero_portrait_morvaenthir.gd")
const MORVAETH_PAINTER = preload("res://scripts/ui/hero_portrait_morvaeth.gd")
const MORVAETH2_PAINTER = preload("res://scripts/ui/hero_portrait_morvaeth2.gd")
const MORVAKHUL_PAINTER = preload("res://scripts/ui/hero_portrait_morvakhul.gd")
const MORVATH_PAINTER = preload("res://scripts/ui/hero_portrait_morvath.gd")
const MORVEIN_PAINTER = preload("res://scripts/ui/hero_portrait_morvein.gd")
const MORVEKHAR_PAINTER = preload("res://scripts/ui/hero_portrait_morvekhar.gd")
const MORVYSSK_PAINTER = preload("res://scripts/ui/hero_portrait_morvyssk.gd")
const NARAKA_PAINTER = preload("res://scripts/ui/hero_portrait_naraka.gd")
const NAZULMOR_PAINTER = preload("res://scripts/ui/hero_portrait_nazulmor.gd")
const NEXTHYRIUS_PAINTER = preload("res://scripts/ui/hero_portrait_nexthyrius.gd")
const NIXWEAVER_PAINTER = preload("res://scripts/ui/hero_portrait_nixweaver.gd")
const NYRELLIETH_PAINTER = preload("res://scripts/ui/hero_portrait_nyrellieth.gd")
const NYRETHZALV_PAINTER = preload("res://scripts/ui/hero_portrait_nyrethzalv.gd")
const NYXARA_PAINTER = preload("res://scripts/ui/hero_portrait_nyxara.gd")
const NYXARATH_PAINTER = preload("res://scripts/ui/hero_portrait_nyxarath.gd")
const NYXARETH_PAINTER = preload("res://scripts/ui/hero_portrait_nyxareth.gd")
const NYXAREVA_PAINTER = preload("res://scripts/ui/hero_portrait_nyxareva.gd")
const NYXARIEL_PAINTER = preload("res://scripts/ui/hero_portrait_nyxariel.gd")
const NYXARIS_PAINTER = preload("res://scripts/ui/hero_portrait_nyxaris.gd")
const NYXAROTH_PAINTER = preload("res://scripts/ui/hero_portrait_nyxaroth.gd")
const NYXHARR_PAINTER = preload("res://scripts/ui/hero_portrait_nyxharr.gd")
const NYXRAAL_PAINTER = preload("res://scripts/ui/hero_portrait_nyxraal.gd")
const NYXTHRAEL_PAINTER = preload("res://scripts/ui/hero_portrait_nyxthrael.gd")
const NYZRAK_PAINTER = preload("res://scripts/ui/hero_portrait_nyzrak.gd")
const OBANAI_PAINTER = preload("res://scripts/ui/hero_portrait_obanai.gd")
const PYRAENA_PAINTER = preload("res://scripts/ui/hero_portrait_pyraena.gd")
const PYRAETHIS_PAINTER = preload("res://scripts/ui/hero_portrait_pyraethis.gd")
const PYRAKLOS_PAINTER = preload("res://scripts/ui/hero_portrait_pyraklos.gd")
const PYRENTH_PAINTER = preload("res://scripts/ui/hero_portrait_pyrenth.gd")
const PYRHAAN_PAINTER = preload("res://scripts/ui/hero_portrait_pyrhaan.gd")
const RAKZHAN_PAINTER = preload("res://scripts/ui/hero_portrait_rakzhan.gd")
const RAVOKKAR_PAINTER = preload("res://scripts/ui/hero_portrait_ravokkar.gd")
const RAZAK_PAINTER = preload("res://scripts/ui/hero_portrait_razak.gd")
const RYNVARA_PAINTER = preload("res://scripts/ui/hero_portrait_rynvara.gd")
const SANGUIRE_PAINTER = preload("res://scripts/ui/hero_portrait_sanguire.gd")
const SANGUIVETH_PAINTER = preload("res://scripts/ui/hero_portrait_sanguiveth.gd")
const SASORI_PAINTER = preload("res://scripts/ui/hero_portrait_sasori.gd")
const SEIRYUKONG_PAINTER = preload("res://scripts/ui/hero_portrait_seiryukong.gd")
const SELUNARA_PAINTER = preload("res://scripts/ui/hero_portrait_selunara.gd")
const SERAPHIENNE_PAINTER = preload("res://scripts/ui/hero_portrait_seraphienne.gd")
const SETHRAKHAR_PAINTER = preload("res://scripts/ui/hero_portrait_sethrakhar.gd")
const SHIMORAKH_PAINTER = preload("res://scripts/ui/hero_portrait_shimorakh.gd")
const SHIROTAKA_PAINTER = preload("res://scripts/ui/hero_portrait_shirotaka.gd")
const SIRAKZAN_PAINTER = preload("res://scripts/ui/hero_portrait_sirakzan.gd")
const SOLARA_PAINTER = preload("res://scripts/ui/hero_portrait_solara.gd")
const SOLARETH_PAINTER = preload("res://scripts/ui/hero_portrait_solareth.gd")
const SOLVANTH_PAINTER = preload("res://scripts/ui/hero_portrait_solvanth.gd")
const SOLVARIN_PAINTER = preload("res://scripts/ui/hero_portrait_solvarin.gd")
const SUNAKAGE_PAINTER = preload("res://scripts/ui/hero_portrait_sunakage.gd")
const SYLVANTHEROS_PAINTER = preload("res://scripts/ui/hero_portrait_sylvantheros.gd")
const SYRENTHA_PAINTER = preload("res://scripts/ui/hero_portrait_syrentha.gd")
const SYRINDRA_PAINTER = preload("res://scripts/ui/hero_portrait_syrindra.gd")
const THALAKRYON_PAINTER = preload("res://scripts/ui/hero_portrait_thalakryon.gd")
const THALGRYN_PAINTER = preload("res://scripts/ui/hero_portrait_thalgryn.gd")
const THALRYNDEL_PAINTER = preload("res://scripts/ui/hero_portrait_thalryndel.gd")
const THORAZ_PAINTER = preload("res://scripts/ui/hero_portrait_thoraz.gd")
const THORNVAEGRIM_PAINTER = preload("res://scripts/ui/hero_portrait_thornvaegrim.gd")
const THORVAK_PAINTER = preload("res://scripts/ui/hero_portrait_thorvak.gd")
const THORVIN_PAINTER = preload("res://scripts/ui/hero_portrait_thorvin.gd")
const TSUKIYORA_PAINTER = preload("res://scripts/ui/hero_portrait_tsukiyora.gd")
const URGHARUN_PAINTER = preload("res://scripts/ui/hero_portrait_urgharun.gd")
const URSATH_PAINTER = preload("res://scripts/ui/hero_portrait_ursath.gd")
const VAELINDRA_PAINTER = preload("res://scripts/ui/hero_portrait_vaelindra.gd")
const VAELKORR_PAINTER = preload("res://scripts/ui/hero_portrait_vaelkorr.gd")
const VAELMYRRA_PAINTER = preload("res://scripts/ui/hero_portrait_vaelmyrra.gd")
const VAERITH_PAINTER = preload("res://scripts/ui/hero_portrait_vaerith.gd")
const VALEKRIS_PAINTER = preload("res://scripts/ui/hero_portrait_valekris.gd")
const VALTHAR_PAINTER = preload("res://scripts/ui/hero_portrait_valthar.gd")
const VARDROK_PAINTER = preload("res://scripts/ui/hero_portrait_vardrok.gd")
const VARGRATH_PAINTER = preload("res://scripts/ui/hero_portrait_vargrath.gd")
const VARGROTH_PAINTER = preload("res://scripts/ui/hero_portrait_vargroth.gd")
const VARKUL_PAINTER = preload("res://scripts/ui/hero_portrait_varkul.gd")
const VELMYRTH_PAINTER = preload("res://scripts/ui/hero_portrait_velmyrth.gd")
const VERDANIX_PAINTER = preload("res://scripts/ui/hero_portrait_verdanix.gd")
const VESHTRAX_PAINTER = preload("res://scripts/ui/hero_portrait_veshtrax.gd")
const VESSYRA_PAINTER = preload("res://scripts/ui/hero_portrait_vessyra.gd")
const VHAERITH_PAINTER = preload("res://scripts/ui/hero_portrait_vhaerith.gd")
const VHALZUN_PAINTER = preload("res://scripts/ui/hero_portrait_vhalzun.gd")
const VHORETHZIR_PAINTER = preload("res://scripts/ui/hero_portrait_vhorethzir.gd")
const VHYSSARION_PAINTER = preload("res://scripts/ui/hero_portrait_vhyssarion.gd")
const VOKRAHN_PAINTER = preload("res://scripts/ui/hero_portrait_vokrahn.gd")
const VORENMARR_PAINTER = preload("res://scripts/ui/hero_portrait_vorenmarr.gd")
const VORGATH_PAINTER = preload("res://scripts/ui/hero_portrait_vorgath.gd")
const VORTHAKUL_PAINTER = preload("res://scripts/ui/hero_portrait_vorthakul.gd")
const VRASKHAN_PAINTER = preload("res://scripts/ui/hero_portrait_vraskhan.gd")
const VULKARETH_PAINTER = preload("res://scripts/ui/hero_portrait_vulkareth.gd")
const VYRAETH_PAINTER = preload("res://scripts/ui/hero_portrait_vyraeth.gd")
const WIRO_PAINTER = preload("res://scripts/ui/hero_portrait_wiro.gd")
const XAELMORAN_PAINTER = preload("res://scripts/ui/hero_portrait_xaelmoran.gd")
const XAERISSA_PAINTER = preload("res://scripts/ui/hero_portrait_xaerissa.gd")
const XARETH_PAINTER = preload("res://scripts/ui/hero_portrait_xareth.gd")
const XARNTHUUL_PAINTER = preload("res://scripts/ui/hero_portrait_xarnthuul.gd")
const XELNARATH_PAINTER = preload("res://scripts/ui/hero_portrait_xelnarath.gd")
const XERAKHOTEP_PAINTER = preload("res://scripts/ui/hero_portrait_xerakhotep.gd")
const XERAKKUTH_PAINTER = preload("res://scripts/ui/hero_portrait_xerakkuth.gd")
const XERATHIS_PAINTER = preload("res://scripts/ui/hero_portrait_xerathis.gd")
const XIRTHALIS_PAINTER = preload("res://scripts/ui/hero_portrait_xirthalis.gd")
const XYRAEL_PAINTER = preload("res://scripts/ui/hero_portrait_xyrael.gd")
const YAMAKO_PAINTER = preload("res://scripts/ui/hero_portrait_yamako.gd")
const YHORANTH_PAINTER = preload("res://scripts/ui/hero_portrait_yhoranth.gd")
const YOMIGETSU_PAINTER = preload("res://scripts/ui/hero_portrait_yomigetsu.gd")
const ZAHKARETH_PAINTER = preload("res://scripts/ui/hero_portrait_zahkareth.gd")
const ZARETHYR_PAINTER = preload("res://scripts/ui/hero_portrait_zarethyr.gd")
const ZHAERIS_PAINTER = preload("res://scripts/ui/hero_portrait_zhaeris.gd")
const ZHARAKZUUL_PAINTER = preload("res://scripts/ui/hero_portrait_zharakzuul.gd")
const ZHAROK_PAINTER = preload("res://scripts/ui/hero_portrait_zharok.gd")
const ZORASHI_PAINTER = preload("res://scripts/ui/hero_portrait_zorashi.gd")
const ZOROTHRAX_PAINTER = preload("res://scripts/ui/hero_portrait_zorothrax.gd")
const ZULKHAVEN_PAINTER = preload("res://scripts/ui/hero_portrait_zulkhaven.gd")
const ZYVARETH_PAINTER = preload("res://scripts/ui/hero_portrait_zyvareth.gd")


static func ids() -> Array[String]:
	return [
		"kaedrin",
		"kaeldris",
		"kaelthar",
		"kaelthorn",
		"kaelthys",
		"kaelvyrn",
		"kaerinya",
		"kaervosth",
		"kagetsuka",
		"kaineroth",
		"kairenji",
		"kaithros",
		"kaizoku_raijin",
		"kaoruken",
		"karzhul",
		"kassadin",
		"kazuren",
		"kazureth",
		"kenshiro",
		"khalros",
		"khalzaredh",
		"khazan",
		"korokai",
		"krobellus",
		"krognarr",
		"kryvoxar",
		"kurogari",
		"kyrenzai",
		"kyumirra",
		"leoric",
		"luminar",
		"lyrenya",
		"lyrienne",
		"lyssarethys",
		"malzareth",
		"malzeroth",
		"molgravar",
		"morkhaera",
		"morkhelvis",
		"morthyrax",
		"morvaenthir",
		"morvaeth",
		"morvaeth2",
		"morvakhul",
		"morvath",
		"morvein",
		"morvekhar",
		"morvyssk",
		"naraka",
		"nazulmor",
		"nexthyrius",
		"nixweaver",
		"nyrellieth",
		"nyrethzalv",
		"nyxara",
		"nyxarath",
		"nyxareth",
		"nyxareva",
		"nyxariel",
		"nyxaris",
		"nyxaroth",
		"nyxharr",
		"nyxraal",
		"nyxthrael",
		"nyzrak",
		"obanai",
		"pyraena",
		"pyraethis",
		"pyraklos",
		"pyrenth",
		"pyrhaan",
		"rakzhan",
		"ravokkar",
		"razak",
		"rynvara",
		"sanguire",
		"sanguiveth",
		"sasori",
		"seiryukong",
		"selunara",
		"seraphienne",
		"sethrakhar",
		"shimorakh",
		"shirotaka",
		"sirakzan",
		"solara",
		"solareth",
		"solvanth",
		"solvarin",
		"sunakage",
		"sylvantheros",
		"syrentha",
		"syrindra",
		"thalakryon",
		"thalgryn",
		"thalryndel",
		"thoraz",
		"thornvaegrim",
		"thorvak",
		"thorvin",
		"tsukiyora",
		"urgharun",
		"ursath",
		"vaelindra",
		"vaelkorr",
		"vaelmyrra",
		"vaerith",
		"valekris",
		"valthar",
		"vardrok",
		"vargrath",
		"vargroth",
		"varkul",
		"velmyrth",
		"verdanix",
		"veshtrax",
		"vessyra",
		"vhaerith",
		"vhalzun",
		"vhorethzir",
		"vhyssarion",
		"vokrahn",
		"vorenmarr",
		"vorgath",
		"vorthakul",
		"vraskhan",
		"vulkareth",
		"vyraeth",
		"wiro",
		"xaelmoran",
		"xaerissa",
		"xareth",
		"xarnthuul",
		"xelnarath",
		"xerakhotep",
		"xerakkuth",
		"xerathis",
		"xirthalis",
		"xyrael",
		"yamako",
		"yhoranth",
		"yomigetsu",
		"zahkareth",
		"zarethyr",
		"zhaeris",
		"zharakzuul",
		"zharok",
		"zorashi",
		"zorothrax",
		"zulkhaven",
		"zyvareth"
	]


static func has_custom(id: String) -> bool:
	return id in ids()


static func paint(canvas: CanvasItem, box: Rect2, id: String) -> void:
	match id:
		"kaedrin":
			KAEDRIN_PAINTER.paint(canvas, box)
		"kaeldris":
			KAELDRIS_PAINTER.paint(canvas, box)
		"kaelthar":
			KAELTHAR_PAINTER.paint(canvas, box)
		"kaelthorn":
			KAELTHORN_PAINTER.paint(canvas, box)
		"kaelthys":
			KAELTHYS_PAINTER.paint(canvas, box)
		"kaelvyrn":
			KAELVYRN_PAINTER.paint(canvas, box)
		"kaerinya":
			KAERINYA_PAINTER.paint(canvas, box)
		"kaervosth":
			KAERVOSTH_PAINTER.paint(canvas, box)
		"kagetsuka":
			KAGETSUKA_PAINTER.paint(canvas, box)
		"kaineroth":
			KAINEROTH_PAINTER.paint(canvas, box)
		"kairenji":
			KAIRENJI_PAINTER.paint(canvas, box)
		"kaithros":
			KAITHROS_PAINTER.paint(canvas, box)
		"kaizoku_raijin":
			KAIZOKU_RAIJIN_PAINTER.paint(canvas, box)
		"kaoruken":
			KAORUKEN_PAINTER.paint(canvas, box)
		"karzhul":
			KARZHUL_PAINTER.paint(canvas, box)
		"kassadin":
			KASSADIN_PAINTER.paint(canvas, box)
		"kazuren":
			KAZUREN_PAINTER.paint(canvas, box)
		"kazureth":
			KAZURETH_PAINTER.paint(canvas, box)
		"kenshiro":
			KENSHIRO_PAINTER.paint(canvas, box)
		"khalros":
			KHALROS_PAINTER.paint(canvas, box)
		"khalzaredh":
			KHALZAREDH_PAINTER.paint(canvas, box)
		"khazan":
			KHAZAN_PAINTER.paint(canvas, box)
		"korokai":
			KOROKAI_PAINTER.paint(canvas, box)
		"krobellus":
			KROBELLUS_PAINTER.paint(canvas, box)
		"krognarr":
			KROGNARR_PAINTER.paint(canvas, box)
		"kryvoxar":
			KRYVOXAR_PAINTER.paint(canvas, box)
		"kurogari":
			KUROGARI_PAINTER.paint(canvas, box)
		"kyrenzai":
			KYRENZAI_PAINTER.paint(canvas, box)
		"kyumirra":
			KYUMIRRA_PAINTER.paint(canvas, box)
		"leoric":
			LEORIC_PAINTER.paint(canvas, box)
		"luminar":
			LUMINAR_PAINTER.paint(canvas, box)
		"lyrenya":
			LYRENYA_PAINTER.paint(canvas, box)
		"lyrienne":
			LYRIENNE_PAINTER.paint(canvas, box)
		"lyssarethys":
			LYSSARETHYS_PAINTER.paint(canvas, box)
		"malzareth":
			MALZARETH_PAINTER.paint(canvas, box)
		"malzeroth":
			MALZEROTH_PAINTER.paint(canvas, box)
		"molgravar":
			MOLGRAVAR_PAINTER.paint(canvas, box)
		"morkhaera":
			MORKHAERA_PAINTER.paint(canvas, box)
		"morkhelvis":
			MORKHELVIS_PAINTER.paint(canvas, box)
		"morthyrax":
			MORTHYRAX_PAINTER.paint(canvas, box)
		"morvaenthir":
			MORVAENTHIR_PAINTER.paint(canvas, box)
		"morvaeth":
			MORVAETH_PAINTER.paint(canvas, box)
		"morvaeth2":
			MORVAETH2_PAINTER.paint(canvas, box)
		"morvakhul":
			MORVAKHUL_PAINTER.paint(canvas, box)
		"morvath":
			MORVATH_PAINTER.paint(canvas, box)
		"morvein":
			MORVEIN_PAINTER.paint(canvas, box)
		"morvekhar":
			MORVEKHAR_PAINTER.paint(canvas, box)
		"morvyssk":
			MORVYSSK_PAINTER.paint(canvas, box)
		"naraka":
			NARAKA_PAINTER.paint(canvas, box)
		"nazulmor":
			NAZULMOR_PAINTER.paint(canvas, box)
		"nexthyrius":
			NEXTHYRIUS_PAINTER.paint(canvas, box)
		"nixweaver":
			NIXWEAVER_PAINTER.paint(canvas, box)
		"nyrellieth":
			NYRELLIETH_PAINTER.paint(canvas, box)
		"nyrethzalv":
			NYRETHZALV_PAINTER.paint(canvas, box)
		"nyxara":
			NYXARA_PAINTER.paint(canvas, box)
		"nyxarath":
			NYXARATH_PAINTER.paint(canvas, box)
		"nyxareth":
			NYXARETH_PAINTER.paint(canvas, box)
		"nyxareva":
			NYXAREVA_PAINTER.paint(canvas, box)
		"nyxariel":
			NYXARIEL_PAINTER.paint(canvas, box)
		"nyxaris":
			NYXARIS_PAINTER.paint(canvas, box)
		"nyxaroth":
			NYXAROTH_PAINTER.paint(canvas, box)
		"nyxharr":
			NYXHARR_PAINTER.paint(canvas, box)
		"nyxraal":
			NYXRAAL_PAINTER.paint(canvas, box)
		"nyxthrael":
			NYXTHRAEL_PAINTER.paint(canvas, box)
		"nyzrak":
			NYZRAK_PAINTER.paint(canvas, box)
		"obanai":
			OBANAI_PAINTER.paint(canvas, box)
		"pyraena":
			PYRAENA_PAINTER.paint(canvas, box)
		"pyraethis":
			PYRAETHIS_PAINTER.paint(canvas, box)
		"pyraklos":
			PYRAKLOS_PAINTER.paint(canvas, box)
		"pyrenth":
			PYRENTH_PAINTER.paint(canvas, box)
		"pyrhaan":
			PYRHAAN_PAINTER.paint(canvas, box)
		"rakzhan":
			RAKZHAN_PAINTER.paint(canvas, box)
		"ravokkar":
			RAVOKKAR_PAINTER.paint(canvas, box)
		"razak":
			RAZAK_PAINTER.paint(canvas, box)
		"rynvara":
			RYNVARA_PAINTER.paint(canvas, box)
		"sanguire":
			SANGUIRE_PAINTER.paint(canvas, box)
		"sanguiveth":
			SANGUIVETH_PAINTER.paint(canvas, box)
		"sasori":
			SASORI_PAINTER.paint(canvas, box)
		"seiryukong":
			SEIRYUKONG_PAINTER.paint(canvas, box)
		"selunara":
			SELUNARA_PAINTER.paint(canvas, box)
		"seraphienne":
			SERAPHIENNE_PAINTER.paint(canvas, box)
		"sethrakhar":
			SETHRAKHAR_PAINTER.paint(canvas, box)
		"shimorakh":
			SHIMORAKH_PAINTER.paint(canvas, box)
		"shirotaka":
			SHIROTAKA_PAINTER.paint(canvas, box)
		"sirakzan":
			SIRAKZAN_PAINTER.paint(canvas, box)
		"solara":
			SOLARA_PAINTER.paint(canvas, box)
		"solareth":
			SOLARETH_PAINTER.paint(canvas, box)
		"solvanth":
			SOLVANTH_PAINTER.paint(canvas, box)
		"solvarin":
			SOLVARIN_PAINTER.paint(canvas, box)
		"sunakage":
			SUNAKAGE_PAINTER.paint(canvas, box)
		"sylvantheros":
			SYLVANTHEROS_PAINTER.paint(canvas, box)
		"syrentha":
			SYRENTHA_PAINTER.paint(canvas, box)
		"syrindra":
			SYRINDRA_PAINTER.paint(canvas, box)
		"thalakryon":
			THALAKRYON_PAINTER.paint(canvas, box)
		"thalgryn":
			THALGRYN_PAINTER.paint(canvas, box)
		"thalryndel":
			THALRYNDEL_PAINTER.paint(canvas, box)
		"thoraz":
			THORAZ_PAINTER.paint(canvas, box)
		"thornvaegrim":
			THORNVAEGRIM_PAINTER.paint(canvas, box)
		"thorvak":
			THORVAK_PAINTER.paint(canvas, box)
		"thorvin":
			THORVIN_PAINTER.paint(canvas, box)
		"tsukiyora":
			TSUKIYORA_PAINTER.paint(canvas, box)
		"urgharun":
			URGHARUN_PAINTER.paint(canvas, box)
		"ursath":
			URSATH_PAINTER.paint(canvas, box)
		"vaelindra":
			VAELINDRA_PAINTER.paint(canvas, box)
		"vaelkorr":
			VAELKORR_PAINTER.paint(canvas, box)
		"vaelmyrra":
			VAELMYRRA_PAINTER.paint(canvas, box)
		"vaerith":
			VAERITH_PAINTER.paint(canvas, box)
		"valekris":
			VALEKRIS_PAINTER.paint(canvas, box)
		"valthar":
			VALTHAR_PAINTER.paint(canvas, box)
		"vardrok":
			VARDROK_PAINTER.paint(canvas, box)
		"vargrath":
			VARGRATH_PAINTER.paint(canvas, box)
		"vargroth":
			VARGROTH_PAINTER.paint(canvas, box)
		"varkul":
			VARKUL_PAINTER.paint(canvas, box)
		"velmyrth":
			VELMYRTH_PAINTER.paint(canvas, box)
		"verdanix":
			VERDANIX_PAINTER.paint(canvas, box)
		"veshtrax":
			VESHTRAX_PAINTER.paint(canvas, box)
		"vessyra":
			VESSYRA_PAINTER.paint(canvas, box)
		"vhaerith":
			VHAERITH_PAINTER.paint(canvas, box)
		"vhalzun":
			VHALZUN_PAINTER.paint(canvas, box)
		"vhorethzir":
			VHORETHZIR_PAINTER.paint(canvas, box)
		"vhyssarion":
			VHYSSARION_PAINTER.paint(canvas, box)
		"vokrahn":
			VOKRAHN_PAINTER.paint(canvas, box)
		"vorenmarr":
			VORENMARR_PAINTER.paint(canvas, box)
		"vorgath":
			VORGATH_PAINTER.paint(canvas, box)
		"vorthakul":
			VORTHAKUL_PAINTER.paint(canvas, box)
		"vraskhan":
			VRASKHAN_PAINTER.paint(canvas, box)
		"vulkareth":
			VULKARETH_PAINTER.paint(canvas, box)
		"vyraeth":
			VYRAETH_PAINTER.paint(canvas, box)
		"wiro":
			WIRO_PAINTER.paint(canvas, box)
		"xaelmoran":
			XAELMORAN_PAINTER.paint(canvas, box)
		"xaerissa":
			XAERISSA_PAINTER.paint(canvas, box)
		"xareth":
			XARETH_PAINTER.paint(canvas, box)
		"xarnthuul":
			XARNTHUUL_PAINTER.paint(canvas, box)
		"xelnarath":
			XELNARATH_PAINTER.paint(canvas, box)
		"xerakhotep":
			XERAKHOTEP_PAINTER.paint(canvas, box)
		"xerakkuth":
			XERAKKUTH_PAINTER.paint(canvas, box)
		"xerathis":
			XERATHIS_PAINTER.paint(canvas, box)
		"xirthalis":
			XIRTHALIS_PAINTER.paint(canvas, box)
		"xyrael":
			XYRAEL_PAINTER.paint(canvas, box)
		"yamako":
			YAMAKO_PAINTER.paint(canvas, box)
		"yhoranth":
			YHORANTH_PAINTER.paint(canvas, box)
		"yomigetsu":
			YOMIGETSU_PAINTER.paint(canvas, box)
		"zahkareth":
			ZAHKARETH_PAINTER.paint(canvas, box)
		"zarethyr":
			ZARETHYR_PAINTER.paint(canvas, box)
		"zhaeris":
			ZHAERIS_PAINTER.paint(canvas, box)
		"zharakzuul":
			ZHARAKZUUL_PAINTER.paint(canvas, box)
		"zharok":
			ZHAROK_PAINTER.paint(canvas, box)
		"zorashi":
			ZORASHI_PAINTER.paint(canvas, box)
		"zorothrax":
			ZOROTHRAX_PAINTER.paint(canvas, box)
		"zulkhaven":
			ZULKHAVEN_PAINTER.paint(canvas, box)
		"zyvareth":
			ZYVARETH_PAINTER.paint(canvas, box)
		_:
			pass
