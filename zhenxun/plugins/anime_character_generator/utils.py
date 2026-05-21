import random

# 画师风格套装
ARTIST_STYLES = {
    # "雪糕4件套": "artist: ciloranko, [Artist: Sho_(sho_LWLW)], [Artist: baku-p], [Artist: Tsubasa_tsubasa]",
    # "可爱4件套": "artist:ciloranko , [artist:sho_(sho_lwlw)], [[artist:tianliang_duohe_fangdongye]],[[[[[[artist:kani_biimu]]]]]]",
    # "可爱6件套": "artist:ciloranko, [artist:tianliang duohe fangdongye], [artist:sho_(sho_lwlw)], [artist:baku-p], [artist:aki99]",
    # "萝莉5件套": "artist:ciloranko, [artist:tianliang duohe fangdongye], [artist:sho_(sho_lwlw)], [artist:baku-p], [artist:tsubasa_tsubasa]",
    # "萝莉7件套": "artist: ciloranko, [artist: tianliang duohe fangdongye], [artist: sho_(sho_lwlw)], [artist: baku-p], [artist:tsubasa_tsubasa], [[artist:as109]], [[artist:rhasta]]",
    "水彩画风": "{hokori sakuni}, {ciloranko}, {ke-ta}, {houkisei},{kedama milk}",
    # "动画画风": "artist:pu hua, artist:shiratamaco, artist:tianliang duohe fangdongye",
    # "海报画风": "artist:ciloranko, {artist:menthako}, {artist:tianliang duohe fangdongye}, [artist:sho (sho lwlw)], [artist:baku-p], [[[artist:tsubasa tsubasa]]], artist: kemo camotli",
    "鲜艳色彩画风": "[artist:ningen_mame], {{{ciloranko}}}, [artist:sho_(sho_lwlw)], [[artist:rhasta]], [artist:wlop], [artist:ke-ta]",
    "熟女": "1.3::artist:Rhasta,artist:kcccc,::,artist:modare,artist:yoneyama_mai,artist:piromizu,shiny_skin,",
    "少女": "{hokori sakuni}, {ciloranko}, {ke-ta}, {houkisei},{kedama milk},",
    "萝莉": "artist:ciloranko, [artist:sho_(sho_lwlw)], [artist:baku-p], ",
}

# 角色数据字典
CHARACTER_DATA = {
    "hair_colors": {
        "streaked_hair": "挑染",
        "xx_colored_inner_hair": "内层挑染",
        "xx_and_xx_hair": "头发内变色",
        "silver_hair": "银发",
        "grey_hair": "灰发",
        "blonde_hair": "金发",
        "brown_hair": "棕色头发",
        "black_hair": "黑发",
        "blue_hair": "蓝发",
        "green_hair": "绿头发",
        "pink_hair": "粉色头发",
        "red_hair": "红头发",
        "platinum_blonde_hair": "铂金色头发",
        "azure_hair": "青色头发",
        "aqua_hair": "水蓝色头发",
        "ruby_hair": "红宝石色头发",
        "two-tone_hair": "两色头发",
        "multicolored_hair": "多色的头发",
        "gradient_hair": "渐变头发",
        "ombre_hair": "渐变头发",
        "split-color_hair": "分色头发",
        "rainbow_hair": "彩虹头发",
    },
    "hair_styles": {
        "straight_hair": "直发",
        "curly_hair": "卷发",
        "wavy_hair": "波浪卷",
        "drill_hair": "钻头发型",
        "hime_cut": "姬发式",
        "bob_cut": "波波发",
        "princess_head": "公主发型",
        "half_up": "上半部分束起",
    },
    "bangs": {
        "forehead": "露额头",
        "hair_flaps": "发瓣",
        "bangs": "刘海",
        "air_bangs": "空气刘海",
        "blunt_bangs": "齐刘海",
        "side_blunt_bangs": "侧面空气刘海",
        "parted_bangs": "中分刘海",
        "swept_bangs": "斜刘海",
        "asymmetric_bangs": "不对称刘海",
        "braided_bangs": "刘海上绑辫子",
    },
    "ponytails": {
        "ponytail": "马尾",
        "twintails": "双马尾",
        "high_ponytail": "高双马尾",
        "low_ponytail": "低双马尾",
        "one_side_up": "披肩单马尾",
        "two_side_up": "披肩双马尾",
        "short_ponytail": "短马尾",
        "side_ponytail": "侧马尾",
        "tied_hair": "扎过的头发",
        "low_tied_hair": "低扎头发",
        "multi_tied_hair": "多扎头发",
    },
    "braids": {
        "braid": "辫子",
        "french_braid": "法式辫子",
        "braiding_hair": "辫子头发",
        "side_braid": "侧辫",
        "twin_braids": "双辫子",
        "three_strand_braid": "三股辫",
        "short_braid": "短辫子",
        "long_braid": "长辫子",
        "braided_bun": "辫式发髻",
        "braided_ponytail": "麻花辫马尾",
        "crown_braid": "法式冠编发",
        "multiple_braids": "多股辫",
        "single_braid": "单股辫",
    },
    "buns": {"double_bun": "丸子头", "hair_bun": "圆发髻", "ballet_hair_bun": "芭蕾髻"},
    "special_hair": {
        "pointy_hair": "尖头头发",
        "feather_hair": "羽毛头发",
        "bow_shaped_hair": "弓形头发",
        "lone_nape_hair": "孤颈头发",
        "alternate_hairstyle": "变换发型",
        "ahoge": "短呆毛",
        "heart_ahoge": "心形呆毛",
        "antenna_hair": "长呆毛",
        "sideburns": "鬓角",
        "long_sideburns": "长鬓角",
        "sidelocks": "侧边发辫",
        "bald": "秃头",
        "afro": "爆炸头",
        "spiked_hair": "尖刺头发",
    },
    "eye_colors": {
        "silver_eyes": "银色眼睛",
        "grey_eyes": "灰色眼睛",
        "blonde_eyes": "金色眼睛",
        "brown_eyes": "棕色眼睛",
        "black_eyes": "黑色眼睛",
        "blue_eyes": "蓝色眼睛",
        "green_eyes": "绿色眼睛",
        "pink_eyes": "粉色眼睛",
        "red_eyes": "红色眼睛",
        "aqua_eyes": "青色眼睛",
        "multicolored_eyes": "多彩眼睛",
        "gradient_eyes": "渐变眼睛",
        "heterochromia": "异色瞳",
    },
    "eye_types": {
        "light_eyes": "明亮的眼睛",
        "glowing_eye": "发光的眼睛",
        "shiny_eyes": "闪亮的眼睛",
        "sparkling_eyes": "星星眼",
        "anime_style_eyes": "动画眼",
        "water_eyes": "水汪汪的眼睛",
        "beautiful_detailed_eyes": "美丽的眼睛",
        "solid_oval_eyes": "Q版实心椭圆眼睛",
        "solid_circle_pupils": "Q版实心圆瞳孔",
        "heart_in_eye": "心形眼",
        "sparkling_anime_eyes": "闪光动画眼",
        "solid_eyes": "坚定的眼睛",
    },
    "pupils": {
        "pupils": "瞳孔",
        "bright_pupils": "明亮的瞳孔",
        "slit_pupils": "竖瞳孔/猫眼",
        "snake_pupils": "蛇瞳孔",
        "heart-shaped_pupils": "爱心形瞳孔",
        "diamond-shaped_pupils": "钻石形瞳孔",
        "star-shaped_pupils": "星形瞳孔",
        "dilated_pupils": "瞳孔散大",
        "no_pupils": "没有瞳孔",
        "star_in_eye": "眼睛里的星星",
        "x-shaped_pupils": "X形瞳孔",
        "horizontal_pupils": "水平瞳孔",
        "butterfly-shaped_pupils": "蝴蝶形瞳孔",
        "rectangular_pupils": "长方形瞳孔",
        "square_pupils": "方形瞳孔",
        "dot_pupils": "点瞳孔",
        "extra_pupils": "额外的瞳孔",
        "mismatched_pupils": "不匹配的瞳孔",
        "symbol_in_eye": "眼睛里的符号",
        "cross-shaped_pupils": "十字形瞳孔",
        "purple_pupils": "紫色瞳孔",
        "orange_pupils": "橙色瞳孔",
        "blue_pupils": "蓝色瞳孔",
    },
    "ears": {
        "animal_ears": "兽耳",
        "ears_down": "垂耳",
        "fake_animal_ears": "假兽耳",
        "floppy_ears": "松软的耳朵",
        "animal_ear_fluff": "动物耳朵绒毛",
        "fox_ears": "狐狸耳朵",
        "cat_ears": "猫耳朵",
        "lion_ears": "狮子耳朵",
        "jaguar_ears": "美洲豹耳朵",
        "tiger_ears": "虎耳",
        "dog_ears": "狗耳朵",
        "coyote_ears": "郊狼耳朵",
        "bunny_ears": "兔耳",
        "horse_ears": "马耳",
        "pointy_ears": "尖耳朵",
        "long_pointy_ears": "长尖耳朵",
        "mouse_ears": "老鼠耳朵",
        "raccoon_ears": "浣熊耳朵",
        "squirrel_ears": "松鼠耳朵",
        "bear_ears": "熊耳朵",
        "panda_ears": "熊猫耳朵",
        "bat_ears": "蝙蝠耳朵",
        "robot_ears": "机器人耳朵",
        "extra_ears": "额外的耳朵",
        "ears_through_headwear": "耳朵穿过帽子或头饰",
        "alpaca_ears": "羊驼耳",
    },
    "horns": {
        "horns": "兽角",
        "fake_horns": "假角",
        "dragon_horns": "龙角",
        "oni_horns": "鬼角",
        "antlers": "鹿角",
        "curled_horns": "弯角",
        "goat_horns": "山羊角",
    },
    "chest_size": {
        "flat_chest": "贫乳(A)",
        "small_breasts": "小胸部(B)",
        "medium_breasts": "中等胸部(C)",
        "big_breasts": "大胸部(D)",
        "huge_breasts": "巨乳(E)",
    },
    "formal_wear": {
        "hanfu": "汉服",
        "suit": "西装",
        "tuxedo": "燕尾服",
        "formal_dress": "礼服",
        "evening_gown": "晚礼服",
        "cocktail_dress": "鸡尾酒连衣裙",
        "gown": "女长服",
        "wedding_dress": "婚纱",
        "uchikake": "白无垢(日式嫁衣)",
    },
    "traditional_clothes": {
        "japanese_clothes": "和服",
        "kimono": "和服",
        "sleeveless_kimono": "无袖和服",
        "short_kimono": "短和服",
        "print_kimono": "印花和服",
        "furisode": "振袖和服",
        "obi": "和服腰带",
        "sash": "饰带",
        "cheongsam": "旗袍",
        "china_dress": "中式旗袍",
        "print_cheongsam": "印花旗袍",
        "yukata": "浴衣",
        "chinese_clothes": "唐装",
        "taoist_robe": "道袍",
        "hanbok": "韩服",
        "ao_dai": "越南奥黛",
    },
    "uniforms": {
        "school_uniform": "校服",
        "sailor": "水手服",
        "serafuku": "日式制服",
        "summer_uniform": "夏季制服",
        "kindergarten_uniform": "幼儿园制服",
        "police_uniform": "警服",
        "naval_uniform": "海军制服",
        "military_uniform": "陆军制服",
        "maid": "女仆装",
        "miko": "巫女服",
        "overalls": "工作服",
        "business_suit": "职场制服",
        "nurse": "护士服",
        "chef_uniform": "厨师工装",
        "labcoat": "白大褂",
        "cheerleader": "啦啦队服",
        "band_uniform": "乐队制服",
        "space_suit": "宇航服",
        "leotard": "连衣裤",
    },
    "style_clothes": {
        "chinese_style": "中国风",
        "traditional_clothes": "传统服装",
        "western": "西部风格",
        "german_clothes": "德国服装",
        "gothic": "哥特风格",
        "lolita": "洛丽塔风格",
        "gothic_lolita": "哥特洛丽塔风格",
        "byzantine_fashion": "拜占庭风格",
        "tropical": "热带风格",
        "indian_style": "印度风格",
        "arabian_clothes": "阿拉伯服饰",
        "egyptian_clothes": "埃及风格服饰",
    },
    "costumes": {
        "animal_costume": "动物套装",
        "bunny_costume": "兔子服装",
        "cat_costume": "猫系服装",
        "dog_costume": "狗系服装",
        "bear_costume": "熊套装",
        "santa_costume": "圣诞风格服装",
        "halloween_costume": "万圣节服装",
    },
    "casual_wear": {
        "casual": "休闲装",
        "loungewear": "休闲服",
        "hoodie": "卫衣",
        "homewear": "居家服",
        "pajamas": "睡衣",
        "nightgown": "睡袍",
        "sleepwear": "睡衣套装",
        "print_pajamas": "印花睡衣",
        "polka_dot_pajamas": "波点睡衣",
        "robe": "长袍",
        "cloak": "斗篷",
        "hooded_cloak": "连帽斗篷",
        "winter_clothes": "冬装",
        "down_jacket": "羽绒服",
        "harem_outfit": "舞娘服",
    },
    "sportswear": {
        "sportswear": "运动服",
        "gym_uniform": "体育服",
        "athletic_leotard": "体操服",
        "volleyball_uniform": "排球服",
        "tennis_uniform": "网球衫",
        "baseball_uniform": "棒球服",
        "letterman_jacket": "棒球夹克",
        "biker_clothes": "自行车运动服",
        "bikesuit": "骑行套装",
        "wrestling_outfit": "摔角服",
        "dougi": "武道服",
    },
    "dresses": {
        "dress": "连衣裙",
        "microdress": "微型连衣裙",
        "long_dress": "长连衣裙",
        "off_shoulder_dress": "露肩连衣裙",
        "strapless_dress": "无肩带连衣裙",
        "backless_dress": "露背连衣裙",
        "halter_dress": "绕颈露背吊带裙",
        "sundress": "吊带连衣裙",
        "sleeveless_dress": "无袖连衣裙",
        "sailor_dress": "水手服款裙子",
        "summer_dress": "夏日长裙",
        "pinafore_dress": "围裙连衣裙",
        "sweater_dress": "毛衣连衣裙",
        "armored_dress": "战甲裙",
        "frilled_dress": "花边连衣裙",
        "lace_trimmed_dress": "蕾丝边连衣裙",
        "collared_dress": "有领连衣裙",
        "fur_trimmed_dress": "毛皮镶边连衣裙",
        "layered_dress": "分层连衣裙",
        "pleated_dress": "百褶连衣裙",
        "pencil_dress": "铅笔裙",
        "multicolored_dress": "多色款连衣裙",
        "striped_dress": "条纹连衣裙",
        "plaid_dress": "格子连衣裙",
        "polka_dot_dress": "波点连衣裙",
        "print_dress": "印花连衣裙",
        "see_through_dress": "透视连衣裙",
    },
    "skirts": {
        "skirt": "短裙",
        "microskirt": "超短裙",
        "miniskirt": "迷你裙",
        "skirt_suit": "正装短裙",
        "bikini_skirt": "比基尼裙",
        "pleated_skirt": "百褶裙",
        "pencil_skirt": "短铅笔裙",
        "bubble_skirt": "蓬蓬裙",
        "tutu": "芭蕾舞裙",
        "ballgown": "蓬蓬礼服裙",
        "pettiskirt": "儿童蓬蓬裙",
        "showgirl_skirt": "展会女郎装束",
        "medium_length_skirt": "中等长裙子",
        "beltskirt": "皮带裙",
        "denim_skirt": "牛仔裙",
        "suspender_skirt": "吊带裙",
        "long_skirt": "长裙",
        "summer_long_skirt": "夏日长裙",
        "overskirt": "外裙",
        "hakama_skirt": "袴裙",
        "high_waist_skirt": "高腰裙",
        "kimono_skirt": "和服裙",
        "chiffon_skirt": "雪纺裙",
        "frilled_skirt": "花边裙子",
        "fur_trimmed_skirt": "毛皮镶边短裙",
        "lace_skirt": "蕾丝短裙",
        "layered_skirt": "分层的半裙",
        "print_skirt": "印花短裙",
        "multicolored_skirt": "多色款裙子",
        "striped_skirt": "条纹裙",
        "plaid_skirt": "格子纹短裙",
        "flared_skirt": "伞裙",
        "floral_skirt": "碎花裙",
    },
    "shorts": {
        "shorts": "短裤",
        "micro_shorts": "小尺寸短裤",
        "short_shorts": "热裤",
        "hot_pants": "热裤",
        "cutoffs": "热裤",
        "striped_shorts": "条纹短裤",
        "suspender_shorts": "吊带短裤",
        "denim_shorts": "牛仔短裤",
        "puffy_shorts": "蓬蓬的短裤",
        "dolphin_shorts": "海豚短裤",
        "tight_pants": "紧身裤",
        "briefs": "紧身裤",
        "yoga_pants": "瑜伽裤",
        "track_pants": "运动裤",
        "bike_shorts": "自行车短裤",
        "gym_shorts": "体操短裤",
    },
    "pants": {
        "pants": "长裤",
        "puffy_pants": "蓬松裤",
        "pumpkin_pants": "南瓜裤",
        "hakama_pants": "袴裤",
        "harem_pants": "哈伦裤",
        "bloomers": "灯笼裤",
        "buruma": "超短体操裤",
        "jeans": "牛仔裤",
        "cargo_pants": "工装裤",
        "camouflage_pants": "迷彩裤",
        "capri_pants": "七分裤",
        "chaps": "皮套裤",
        "jumpsuit": "连衫裤",
        "lowleg_pants": "低腰裤子",
        "plaid_pants": "格子呢裤子",
        "striped_pants": "条纹裤",
    },
    "legwear": {
        "bodystocking": "全身袜",
        "pantyhose": "连裤袜",
        "leggings": "裤袜",
        "thighhighs": "长筒袜",
        "kneehighs": "中筒袜",
        "socks": "短袜",
        "black_pantyhose": "黑丝裤袜",
        "white_pantyhose": "白丝裤袜",
        "fishnets": "网袜",
        "fishnet_stockings": "渔网袜",
        "toeless_legwear": "露趾袜",
        "white_thighhighs": "白色长筒袜",
        "black_thighhighs": "黑色长筒袜",
        "pink_thighhighs": "粉色长筒袜",
        "suspenders": "吊带袜",
        "torn_legwear": "破损的裤袜",
        "see_through_legwear": "透明的袜子",
        "frilled_legwear": "花边袜",
        "lace_trimmed_legwear": "蕾丝边袜",
        "striped_legwear": "横条纹袜",
        "polka_dot_legwear": "圆斑袜",
        "print_legwear": "印花袜",
        "over_kneehighs": "过膝袜",
        "bobby_socks": "鲍比袜",
        "tabi": "日式厚底短袜",
        "loose_socks": "泡泡袜",
        "ankle_socks": "踝袜",
        "leg_warmers": "腿套",
        "striped_socks": "横条短袜",
    },
    "accessories": {
        "garters": "袜带",
        "leg_garter": "腿环",
        "garter_straps": "吊带袜的吊带",
        "thigh_strap": "大腿绑带",
        "thigh_ribbon": "大腿缎带",
        "leg_ribbon": "腿缎带",
        "ankle_lace_up": "脚踝系带",
        "thigh_holster": "大腿皮套",
        "arm_garter": "手臂袜带",
    },
    "outerwear": {
        "overcoat": "大衣",
        "coat": "外套",
        "blazer": "西装外套",
        "double_breasted": "双排纽扣",
        "long_coat": "长外套",
        "haori": "羽织",
        "winter_coat": "冬季大衣",
        "hooded_coat": "连帽大衣",
        "fur_coat": "皮草大衣",
        "fur_trimmed_coat": "镶边皮草大衣",
        "duffel_coat": "粗呢大衣",
        "parka": "派克大衣",
        "trench_coat": "风衣",
        "windbreaker": "冲锋衣",
        "raincoat": "雨衣",
        "cape": "披肩",
        "capelet": "小披肩",
        "tunic": "束腰外衣",
        "hagoromo": "羽衣",
    },
    "jackets": {
        "jacket": "夹克衫",
        "open_jacket": "开襟夹克",
        "cropped_jacket": "短款夹克",
        "track_jacket": "运动夹克",
        "hooded_track_jacket": "连帽运动夹克",
        "military_jacket": "军装夹克",
        "camouflage_jacket": "迷彩夹克",
        "leather_jacket": "皮夹克",
        "letterman_jacket": "莱特曼夹克",
        "bomber_jacket": "飞行员夹克",
        "denim_jacket": "牛仔夹克",
        "floating_jacket": "休闲夹克",
        "fur_trimmed_jacket": "毛皮边饰夹克",
        "two_tone_jacket": "两色夹克",
        "down_jacket": "羽绒服",
        "puffer_jacket": "羽绒夹克",
    },
    "sweaters": {
        "sweater": "毛衣",
        "pullover_sweaters": "套头毛衣",
        "ribbed_sweater": "罗纹毛衣",
        "sweater_vest": "毛衣背心",
        "backless_sweater": "露背毛衣",
        "aran_sweater": "爱尔兰毛衣",
        "beige_sweater": "米色毛衣",
        "brown_sweater": "棕色毛衣",
        "hooded_sweater": "连帽毛衣",
        "off_shoulder_sweater": "露肩毛衣",
        "striped_sweater": "条纹毛衣",
        "virgin_killer_sweater": "处男杀手毛衣",
        "fishnet_top": "渔网上衣",
    },
    "footwear": {
        "barefoot": "赤脚",
        "no_shoes": "没有鞋子",
        "shoes": "运动鞋",
        "sneakers": "运动鞋",
        "uwabaki": "室内鞋",
        "platform_footwear": "厚底鞋",
        "high_heels": "高跟鞋",
        "stiletto_heels": "细跟高跟鞋",
        "strappy_heels": "带束带的高跟鞋",
        "platform_heels": "厚底高跟鞋",
        "loafers": "乐福鞋",
        "mary_janes": "珍妮鞋",
        "pointy_footwear": "尖头鞋",
        "winged_footwear": "带翅膀的鞋子",
        "mismatched_footwear": "双色鞋子",
        "brown_footwear": "棕色鞋类",
    },
    "sandals_slippers": {
        "sandals": "凉鞋",
        "barefoot_sandals": "裸足凉鞋",
        "clog_sandals": "木屐凉鞋",
        "geta": "木屐",
        "zouri": "日式草鞋",
        "slippers": "拖鞋",
        "animal_slippers": "动物拖鞋",
        "paw_shoes": "爪子鞋",
        "ballet_slippers": "芭蕾舞鞋",
    },
    "boots": {
        "boots": "靴子",
        "thigh_boots": "大腿靴",
        "knee_boots": "及膝靴",
        "ankle_boots": "踝靴",
        "high_heel_boots": "高跟靴",
        "toeless_boots": "露趾靴",
        "lace_up_boots": "系带靴",
        "cross_laced_footwear": "交叉系带鞋",
        "fur_trimmed_boots": "毛边靴子",
        "snow_boots": "雪地靴",
        "rubber_boots": "胶靴",
        "santa_boots": "圣诞靴",
        "leather_boots": "皮靴",
        "combat_boots": "作战靴",
        "doc_martens": "马丁靴",
        "rain_boots": "雨靴",
    },
    "special_footwear": {
        # "skates": "溜冰鞋",
        # "roller_skates": "旱冰鞋",
        # "inline_skates": "直排轮滑鞋",
        "anklet": "脚环",
        "shackles": "镣铐",
    },
    # 头发长度
    "hair_length": {
        "long_hair": "长发",
        "very_short_hair": "很短的头发",
        "short_hair": "短发",
        "medium_hair": "中等头发",
        "very_long_hair": "很长的头发",
        "absurdly_long_hair": "超级长的头发",
    },
    # 年龄段
    "age_group": {
        "loli": "萝莉",
        "teenage": "青年",
        "mature_female": "熟女",
    },
    # 人物属性 - 职业身份
    "character_roles": {
        "princess": "公主",
        "dancer": "舞者",
        "cheerleader": "啦啦队",
        "ballerina": "芭蕾舞女演员",
        "gym_leader": "体操队队长",
        "waitress": "女服务员",
        "wa_maid": "和风女仆",
        "maid": "女仆",
        "idol": "偶像",
        "kyuudou": "弓道",
        "valkyrie": "女武神",
        "office_lady": "办公室小姐",
        "race_queen": "赛车女郎",
        "witch": "魔女",
        "miko": "巫女",
        "nun": "修女",
        "priest": "牧师",
        "cleric": "神职人员(基督教)",
        "ninja": "忍者",
        "policewoman": "女警",
        "police": "警察",
        "doctor": "医生",
        "nurse": "护士",
        "glasses": "眼镜娘",
        "public_use": "公交车",
        "dominatrix": "女王(SM中)",
        # "yukkuri_shiteitte_ne": "油库里(馒头样人物)",
        "kirisame_marisa_(cosplay)": "cos成雾雨魔理沙",
        "sailor_senshi": "美少女战士",
        "chef": "厨师",
        "mecha": "机甲",
        "mecha_musume": "机娘",
        "humanoid_robot": "类人机器人",
        "cyborg": "半机械人",
    },
    # 人外娘
    "monster_girls": {
        "monster_girl": "人外娘",
        "cat_girl": "猫娘",
        "dog_girl": "犬娘",
        "fox_girl": "狐娘",
        "kitsune": "妖狐",
        "kyuubi": "九尾|九尾狐",
        "raccoon_girl": "浣熊娘",
        "wolf_girl": "狼女孩",
        "bunny_girl": "兔娘",
        "horse_girl": "马娘",
        "cow_girl": "牛娘",
        "dragon_girl": "龙娘",
        "centaur": "人马",
        # "lamia": "蛇娘",
        "mermaid": "美人鱼",
        "slime_musume": "史莱姆娘",
        "spider_girl": "蜘蛛娘",
    },
    # 非人
    "non_human": {
        "angel_and_devil": "天使与恶魔",
        "angel": "天使",
        "devil": "魔鬼（撒旦）",
        "goddess": "女神",
        "elf": "妖精",
        "fairy": "小精灵",
        "dark_elf": "暗精灵",
        "imp": "小恶魔",
        "demon_girl": "恶魔",
        "succubus": "魅魔",
        "vampire": "吸血鬼",
        "magical_girl": "魔法少女",
        "doll": "人偶",
        "giantess": "女巨人",
        "minigirl": "迷你女孩",
        "orc": "兽人",
    },
}


def add_category(category: str, data: dict[str, str]) -> None:
    """添加新的属性分类

    Args:
        category: 分类名称
        data: 属性数据字典 {英文标签: 中文描述}
    """
    CHARACTER_DATA[category] = data


def get_category(category: str) -> dict[str, str] | None:
    """获取指定分类的数据

    Args:
        category: 分类名称

    Returns:
        分类数据字典或None
    """
    return CHARACTER_DATA.get(category)


def get_random_attribute(category: str) -> tuple[str, str] | None:
    """从指定分类中随机获取一个属性

    Args:
        category: 分类名称

    Returns:
        (英文标签, 中文描述) 或 None
    """
    category_data = get_category(category)
    if not category_data:
        return None

    key = random.choice(list(category_data.keys()))
    return key, category_data[key]


def get_all_categories() -> list[str]:
    """获取所有分类名称

    Returns:
        分类名称列表
    """
    return list(CHARACTER_DATA.keys())


# 定义冲突规则：互斥的属性分类组
CONFLICT_GROUPS = {
    # 人物类型冲突组
    "character_type": ["character_roles", "monster_girls", "non_human"],
    # 整身服装冲突组（连衣裙类）
    "full_body_clothing": ["dresses"],
    # 分体服装冲突组（上装类型互斥）
    "separate_clothing": [
        "formal_wear",
        "traditional_clothes",
        "uniforms",
        "style_clothes",
        "costumes",
        "casual_wear",
        "sportswear",
    ],
    # 下装冲突组（下装类型互斥，只在没有整身服装时生效）
    "bottom_wear": ["skirts", "shorts", "pants"],
    # 鞋类冲突组
    "footwear_type": ["footwear", "sandals_slippers", "boots", "special_footwear"],
    # 发型冲突组
    "hairstyle": ["hair_styles", "bangs"],
    # 发型装饰冲突组
    "hair_decoration": ["ponytails", "braids", "buns"],
}

# 定义可选分类（这些分类可能不会被选中）
OPTIONAL_CATEGORIES = {
    "accessories": 0.25,  # 25%概率选择配饰
    "legwear": 0.35,  # 35%概率选择袜类
    "outerwear": 0.2,  # 20%概率选择外套
    "jackets": 0.15,  # 15%概率选择夹克
    "sweaters": 0.15,  # 15%概率选择毛衣
    "special_hair": 0.25,  # 25%概率选择特殊发饰
    "eye_types": 0.15,  # 15%概率选择眼型（不常见）
    "pupils": 0.15,  # 15%概率选择瞳孔（不常见）
    "ears": 0.1,  # 10%概率选择耳朵（不常见）
    "horns": 0.1,  # 10%概率选择角（不常见）
}

# 定义默认属性
DEFAULT_ATTRIBUTES = {
    "age_group": ("teenage", "青年"),  # 默认年龄为青年
}


def generate_random_character(
    categories: list[str] | None = None,
) -> dict[str, tuple[str, str]]:
    """生成随机角色属性

    Args:
        categories: 要生成的分类列表，如果为None则使用所有分类

    Returns:
        {分类名: (英文标签, 中文描述)} 的字典
    """
    if categories is None:
        categories = get_all_categories()

    result = {}
    for category in categories:
        attribute = get_random_attribute(category)
        if attribute:
            result[category] = attribute

    return result


def generate_smart_character() -> dict[str, tuple[str, str]]:
    """智能生成角色属性，避免冲突并处理可选分类

    实现动态概率调整：
    - 整身服装和分体服装互斥
    - 如果没有整身服装，增加分体服装和下装的概率
    - 降低不常见属性的概率

    Returns:
        {分类名: (英文标签, 中文描述)} 的字典
    """
    all_categories = get_all_categories()
    selected_categories = set()
    result = {}
    used_conflict_groups = set()

    # 特殊处理age_group：30%概率是萝莉，50%概率是青年，20%概率是熟女
    if "age_group" in all_categories:
        rand_val = random.random()
        if rand_val < 0.3:
            result["age_group"] = ("loli", "萝莉")  # 30%概率选择萝莉
        elif rand_val < 0.8:
            result["age_group"] = ("teenage", "青年")  # 50%概率选择青年
        else:
            result["age_group"] = ("mature_female", "熟女")  # 20%概率选择熟女
        selected_categories.add("age_group")

    # 特殊处理服装冲突组：整身服装 vs 分体服装
    # 先决定是否选择整身服装
    full_body_categories = CONFLICT_GROUPS.get("full_body_clothing", [])
    available_full_body = [cat for cat in full_body_categories if cat in all_categories]

    if available_full_body and random.random() < 0.3:  # 30%概率选择整身服装
        chosen_category = random.choice(available_full_body)
        selected_categories.add(chosen_category)
        used_conflict_groups.update(full_body_categories)
        used_conflict_groups.update(CONFLICT_GROUPS.get("separate_clothing", []))
        used_conflict_groups.update(CONFLICT_GROUPS.get("bottom_wear", []))
    else:
        # 没有整身服装，处理分体服装
        used_conflict_groups.update(full_body_categories)

        # 增加分体服装概率（从30%提升到70%）
        separate_categories = CONFLICT_GROUPS.get("separate_clothing", [])
        available_separate = [
            cat for cat in separate_categories if cat in all_categories
        ]
        if available_separate and random.random() < 0.7:  # 70%概率选择分体服装
            chosen_category = random.choice(available_separate)
            selected_categories.add(chosen_category)
        used_conflict_groups.update(separate_categories)  # 无论是否选中都要标记为已使用

        # 增加下装概率（从40%提升到80%）
        bottom_categories = CONFLICT_GROUPS.get("bottom_wear", [])
        available_bottom = [cat for cat in bottom_categories if cat in all_categories]
        if available_bottom and random.random() < 0.8:  # 80%概率选择下装
            chosen_category = random.choice(available_bottom)
            selected_categories.add(chosen_category)
        used_conflict_groups.update(bottom_categories)  # 无论是否选中都要标记为已使用

    # 特殊处理character_type组：人类50%，人外25%，非人25%
    character_type_categories = CONFLICT_GROUPS.get("character_type", [])
    available_character_types = [
        cat for cat in character_type_categories if cat in all_categories
    ]
    if available_character_types:
        rand_val = random.random()
        if rand_val < 0.5:  # 50%概率选择人类角色
            if "character_roles" in available_character_types:
                selected_categories.add("character_roles")
        elif rand_val < 0.75:  # 25%概率选择人外
            if "monster_girls" in available_character_types:
                selected_categories.add("monster_girls")
        else:  # 25%概率选择非人
            if "non_human" in available_character_types:
                selected_categories.add("non_human")
        used_conflict_groups.update(character_type_categories)

    # 处理其他冲突组
    for group_name, conflict_categories in CONFLICT_GROUPS.items():
        if group_name in [
            "full_body_clothing",
            "separate_clothing",
            "bottom_wear",
            "character_type",
        ]:
            continue  # 已经处理过了

        available_in_group = [
            cat for cat in conflict_categories if cat in all_categories
        ]
        if available_in_group:
            chosen_category = random.choice(available_in_group)
            selected_categories.add(chosen_category)
            used_conflict_groups.update(conflict_categories)

    # 处理非冲突的必选分类
    for category in all_categories:
        if (
            category not in used_conflict_groups
            and category not in OPTIONAL_CATEGORIES
            and category not in selected_categories
        ):
            selected_categories.add(category)

    # 处理可选分类
    for category, probability in OPTIONAL_CATEGORIES.items():
        if (
            category in all_categories
            and category not in used_conflict_groups
            and category not in selected_categories
        ):
            if random.random() < probability:
                selected_categories.add(category)

    # 为选中的分类生成属性（跳过已有默认值的分类）
    for category in selected_categories:
        if category not in result:
            attribute = get_random_attribute(category)
            if attribute:
                result[category] = attribute

    return result


def format_character_description(character_data: dict[str, tuple[str, str]]) -> str:
    """格式化角色描述

    Args:
        character_data: 角色数据字典

    Returns:
        格式化的角色描述文本
    """
    if not character_data:
        return "无法生成角色描述"

    description_parts = []
    for category, (en_tag, cn_desc) in character_data.items():
        description_parts.append(f"{cn_desc}")

    return "\n".join(description_parts)


def get_random_artist_style() -> tuple[str, str]:
    """随机获取一个画师风格

    Returns:
        (风格名称, 画师提示词) 元组
    """
    style_name = random.choice(list(ARTIST_STYLES.keys()))
    return style_name, ARTIST_STYLES[style_name]


def format_character_with_prompts(
    character_data: dict[str, tuple[str, str]],
    username: str = "角色",
    include_artist_style: bool = True,
) -> tuple[str, str]:
    """格式化角色描述，同时输出key作为prompt和val作为口语化表达

    Args:
        character_data: 角色数据字典
        username: 用户名，用作角色姓名
        include_artist_style: 是否包含画师风格

    Returns:
        (prompts, descriptions) 元组，其中prompts是英文标签，descriptions是中文描述
    """
    if not character_data:
        return "无法生成角色提示词", "无法生成角色描述"

    prompt_parts = []

    # 提取各个属性
    hair_color = "黑色"
    hair_styles = []  # 收集所有发型相关属性
    chest_size = "适中胸部"
    eye_color = "黑色眼睛"
    eye_features = []  # 眼部特征
    clothing = []  # 服装
    footwear = []  # 鞋类
    accessories = []  # 配饰
    character_type = ""  # 角色类型
    special_features = []  # 特殊特征
    background = "神秘的角色"

    for category, (en_tag, cn_desc) in character_data.items():
        prompt_parts.append(en_tag)

        # 根据分类提取对应属性
        if category == "hair_colors":
            hair_color = cn_desc
        elif category in [
            "hair_length",
            "hair_styles",
            "buns",
            "ponytails",
            "braids",
            "bangs",
            "special_hair",
        ]:
            hair_styles.append(cn_desc)
        elif category == "chest_size":
            chest_size = cn_desc
        elif category == "eye_colors":
            eye_color = cn_desc
        elif category in ["eye_types", "pupils"]:
            eye_features.append(cn_desc)
        elif category in [
            "formal_wear",
            "traditional_clothes",
            "uniforms",
            "style_clothes",
            "costumes",
            "casual_wear",
            "sportswear",
            "dresses",
            "skirts",
            "shorts",
            "pants",
            "outerwear",
            "jackets",
            "sweaters",
            "legwear",
        ]:
            clothing.append(cn_desc)
        elif category in ["footwear", "sandals_slippers", "boots", "special_footwear"]:
            footwear.append(cn_desc)
        elif category == "accessories":
            accessories.append(cn_desc)
        elif category in ["character_roles", "monster_girls", "non_human"]:
            character_type = cn_desc
        elif category == "age_group":
            if cn_desc == "萝莉":
                background = "可爱的萝莉"
            elif cn_desc == "青年":
                background = "青春活力的少女"
            elif cn_desc == "熟女":
                background = "成熟魅力的熟女"
        elif category in ["ears", "horns"]:
            special_features.append(cn_desc)
        else:
            # 其他未分类的属性
            special_features.append(cn_desc)

    # 组合发型描述
    if hair_styles:
        hair_style = "的".join(hair_styles) if len(hair_styles) > 1 else hair_styles[0]
    else:
        hair_style = "长发"

    # 组合眼部描述
    eye_desc = eye_color
    if eye_features:
        eye_desc += "，" + "、".join(eye_features)

    # 组合服装描述
    clothing_desc = ""
    if clothing:
        clothing_desc = "穿着" + "、".join(clothing[:3])  # 最多显示3个服装

    # 组合鞋类描述
    footwear_desc = ""
    if footwear:
        footwear_desc = "脚穿" + "、".join(footwear)

    # 组合配饰描述
    accessories_desc = ""
    if accessories:
        accessories_desc = "佩戴" + "、".join(accessories)

    # 组合特殊特征描述
    special_desc = ""
    if special_features:
        special_desc = "具有" + "、".join(special_features[:2])  # 最多显示2个特殊特征

    # 根据年龄组添加对应的画师风格
    if include_artist_style:
        age_style_prompt = ""
        # 检查角色数据中是否有年龄组信息
        for category, (en_tag, cn_desc) in character_data.items():
            if category == "age_group":
                if cn_desc == "萝莉":
                    age_style_prompt = ARTIST_STYLES["萝莉"]
                elif cn_desc == "少女" or cn_desc == "青年":
                    age_style_prompt = ARTIST_STYLES["少女"]
                elif cn_desc == "熟女":
                    age_style_prompt = ARTIST_STYLES["熟女"]
                break
        
        # 如果没有找到年龄组信息，使用默认的少女风格
        if not age_style_prompt:
            age_style_prompt = ARTIST_STYLES["少女"]
        
        prompts = f"{age_style_prompt}, {', '.join(prompt_parts)}"
    else:
        prompts = ", ".join(prompt_parts)

    # 构建完整描述
    desc_parts = [f"二次元转生女孩的“{username}”"]
    desc_parts.append(f"{hair_color}{hair_style}")
    desc_parts.append(f"{chest_size}")
    desc_parts.append(f"瞳色{eye_desc}")

    if character_type:
        desc_parts.append(f"身份是{character_type}")

    if clothing_desc:
        desc_parts.append(clothing_desc)

    if footwear_desc:
        desc_parts.append(footwear_desc)

    if accessories_desc:
        desc_parts.append(accessories_desc)

    if special_desc:
        desc_parts.append(special_desc)

    desc_parts.append(f"是{background}")

    descriptions = "，".join(desc_parts)

    return prompts, descriptions
