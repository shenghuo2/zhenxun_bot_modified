/**
 * Welcome to your Workbox-powered service worker!
 *
 * You'll need to register this file in your web app and you should
 * disable HTTP caching for this file too.
 * See https://goo.gl/nhQhGp
 *
 * The rest of the code is auto-generated. Please don't update this file
 * directly; instead, make changes to your Workbox build configuration
 * and re-run your build process.
 * See https://goo.gl/2aRDsh
 */

importScripts("https://storage.googleapis.com/workbox-cdn/releases/4.3.1/workbox-sw.js");

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

/**
 * The workboxSW.precacheAndRoute() method efficiently caches and responds to
 * requests for URLs in the manifest.
 * See https://goo.gl/S9QRab
 */
self.__precacheManifest = [
  {
    "url": "404.html",
    "revision": "a6d973e11fc84c5fbb11aaf5c1ee99dc"
  },
  {
    "url": "assets/css/0.styles.3af13d03.css",
    "revision": "3cf231b711ffdd04ad7f9a9b68414e7b"
  },
  {
    "url": "assets/img/bg.2cfdbb33.svg",
    "revision": "2cfdbb338a1d44d700b493d7ecbe65d3"
  },
  {
    "url": "assets/img/search.72b0ff46.svg",
    "revision": "72b0ff466169d7f6d483e301dcfe4c00"
  },
  {
    "url": "assets/js/1.10ffbede.js",
    "revision": "30d0f49ced528d8f74d3fc51d5652b85"
  },
  {
    "url": "assets/js/10.1bc41e7e.js",
    "revision": "3518809d3e56ef072be206fcf1f42907"
  },
  {
    "url": "assets/js/11.a588d1ef.js",
    "revision": "6aaa566c2dda40cab2dc64ce163aa792"
  },
  {
    "url": "assets/js/12.cf34d071.js",
    "revision": "a8b90be9a1824824c1b8ec9d0325e117"
  },
  {
    "url": "assets/js/13.e4c4fd17.js",
    "revision": "3a6fb4de3db764975cd9657cf03e1ec9"
  },
  {
    "url": "assets/js/14.98bc494d.js",
    "revision": "42c37b397bf353a5f3be1cee41f69eed"
  },
  {
    "url": "assets/js/15.7ad2daa4.js",
    "revision": "9f04ad1b7ecc7e5a9cd202e36268e12f"
  },
  {
    "url": "assets/js/16.bf4145e4.js",
    "revision": "b710d41e358b55e65f349f6e55ee4aa8"
  },
  {
    "url": "assets/js/17.f29f3e31.js",
    "revision": "e8359c5fdcdb9f437629c5436420c35b"
  },
  {
    "url": "assets/js/18.b1a4fbf5.js",
    "revision": "f2d888fda1b225d3be44e955897d04a7"
  },
  {
    "url": "assets/js/19.1bdaca7e.js",
    "revision": "6b531487d7f2cf458646099809b3916f"
  },
  {
    "url": "assets/js/20.72e363c4.js",
    "revision": "76a3d8f3d2988c2c8bb5ceebd000a862"
  },
  {
    "url": "assets/js/21.f17dd820.js",
    "revision": "13526d937e521fcd12fd176c89f7a122"
  },
  {
    "url": "assets/js/22.39546827.js",
    "revision": "55458e9c00b0418f1c7110cb7624588f"
  },
  {
    "url": "assets/js/23.3280fe28.js",
    "revision": "1b3f8cb448767f1e7d2f11cff6f138df"
  },
  {
    "url": "assets/js/24.7b09bce7.js",
    "revision": "c44500e738708f7085de713364022fc6"
  },
  {
    "url": "assets/js/25.85908063.js",
    "revision": "d3be0c8864323145351123baa6f31d16"
  },
  {
    "url": "assets/js/26.3e679e4f.js",
    "revision": "4e4f60ff60d0764eb2cd6501ed371866"
  },
  {
    "url": "assets/js/27.f8536418.js",
    "revision": "f5162ec7a3857a990891d0c2d267da18"
  },
  {
    "url": "assets/js/28.b2fc4da7.js",
    "revision": "6742ce6d4355d18da344fe5aeb4d930c"
  },
  {
    "url": "assets/js/29.983a5a43.js",
    "revision": "f139bf1bbaa4a3b09bfde97eda98c508"
  },
  {
    "url": "assets/js/3.a9dcdb28.js",
    "revision": "77c3def0358b0b60b343e66acf179866"
  },
  {
    "url": "assets/js/30.4c756d43.js",
    "revision": "3ca6a18a6f9b77a3eedd8f9c335648d9"
  },
  {
    "url": "assets/js/31.cf2fea64.js",
    "revision": "285e56ad6e47eca2ad6816532a81018f"
  },
  {
    "url": "assets/js/32.ad684f9e.js",
    "revision": "4f6169b0c1645ad0c3dee274f5fb4499"
  },
  {
    "url": "assets/js/33.d0ce3830.js",
    "revision": "67a4ededec756d45566655cbf9b4683b"
  },
  {
    "url": "assets/js/34.ad4bc777.js",
    "revision": "6ca3867ac935f5bc1ce1de1c210af673"
  },
  {
    "url": "assets/js/35.1a0d5648.js",
    "revision": "5594783a3cd2485f312872f232688e78"
  },
  {
    "url": "assets/js/36.11e69286.js",
    "revision": "f5e071079243dcaa246f7373cc5c129f"
  },
  {
    "url": "assets/js/37.59fdaf0e.js",
    "revision": "49dc7f9c16ddda737ef0ddf125d6dce8"
  },
  {
    "url": "assets/js/38.64600fdb.js",
    "revision": "07347cc027dc32c00fe9ccde272167bf"
  },
  {
    "url": "assets/js/39.bcc8e7b6.js",
    "revision": "8e09cb213edfadaf7ba6f3cd7a2c8da1"
  },
  {
    "url": "assets/js/4.682beda7.js",
    "revision": "9a5feef2c172c481f443669b47150461"
  },
  {
    "url": "assets/js/40.e3948ff4.js",
    "revision": "937fc44dcb185d9a5ba66ce3ebebd44f"
  },
  {
    "url": "assets/js/41.8afc98e4.js",
    "revision": "d4876b5d9b13d7595f16243ed91dca88"
  },
  {
    "url": "assets/js/42.8abe1e21.js",
    "revision": "c59bda541df412ad3672331efb03fc09"
  },
  {
    "url": "assets/js/43.f67b86fd.js",
    "revision": "1268399fb93c6255c07855b63f0f1c34"
  },
  {
    "url": "assets/js/44.4a378ddb.js",
    "revision": "6644da82e1244255a8d4fa3b2419f2b1"
  },
  {
    "url": "assets/js/45.d1a786ff.js",
    "revision": "6f1acac3160b10b63e581ac78c9c0754"
  },
  {
    "url": "assets/js/46.9a4bb128.js",
    "revision": "222066963141384af1ab11f9f67dfa3c"
  },
  {
    "url": "assets/js/47.102ad60a.js",
    "revision": "490b47547d85ce98871c53c254dcc488"
  },
  {
    "url": "assets/js/48.0ea34501.js",
    "revision": "1cf5a10dac9435fb9b5bbf7d9e3618be"
  },
  {
    "url": "assets/js/49.77e4f78d.js",
    "revision": "437db1f38d0fd0fe17bcd7032944c7d5"
  },
  {
    "url": "assets/js/5.5eec42b2.js",
    "revision": "e4b4c7d0753bf566c6c818cdb00cf668"
  },
  {
    "url": "assets/js/6.45f432e0.js",
    "revision": "60ccde4288669f03337bf24c931065d4"
  },
  {
    "url": "assets/js/7.1ebf8c89.js",
    "revision": "c0e889803a633e4b6f64fb5063c861e8"
  },
  {
    "url": "assets/js/8.1694a43b.js",
    "revision": "90efbbd5750ab55cafb259761b0fe4d1"
  },
  {
    "url": "assets/js/9.8a00c9a2.js",
    "revision": "66408693f07b91abdadf1832bc6faed6"
  },
  {
    "url": "assets/js/app.4f3b2a6a.js",
    "revision": "c7dc0fd0068b699c86a33b9126f5f143"
  },
  {
    "url": "background__.png",
    "revision": "5ac1f0ce419d38cd50f405c8384ef31c"
  },
  {
    "url": "background_.png",
    "revision": "f0cb5c6080cc533cce01b7a7182940fe"
  },
  {
    "url": "background.png",
    "revision": "b65b807cf368e4813b5b876f2a6887a3"
  },
  {
    "url": "blogs/about.html",
    "revision": "a5d7de4b04c7a56d582591854e62092e"
  },
  {
    "url": "categories/index.html",
    "revision": "a0542a64784c255033df679725a09e15"
  },
  {
    "url": "docs/api_doc/group.html",
    "revision": "fef6fb0e2ddfefa92e88b0c3e1c68711"
  },
  {
    "url": "docs/api_doc/plugins.html",
    "revision": "bcdf33d0604abe89a399e4654b50f9c7"
  },
  {
    "url": "docs/api_doc/request.html",
    "revision": "df26d04370ce01f9c2008f38e6a394ed"
  },
  {
    "url": "docs/api_doc/system.html",
    "revision": "1cfc5efc73b1e86eb6ff37b3a6e44049"
  },
  {
    "url": "docs/development_doc/depends.html",
    "revision": "1ff5b06432c443192564923108dc36f8"
  },
  {
    "url": "docs/development_doc/plugins.html",
    "revision": "3d69b09fed576326ff9ebb5df108bdb8"
  },
  {
    "url": "docs/development_doc/shop_handle.html",
    "revision": "762a677f819dee6699335d8d306831e8"
  },
  {
    "url": "docs/development_doc/task_control.html",
    "revision": "f20a15554cf19410ee2a15bbdceeaa2c"
  },
  {
    "url": "docs/development_doc/utils.html",
    "revision": "0da10340c414b442c4fd474d7e5c60e1"
  },
  {
    "url": "docs/faq/index.html",
    "revision": "1081cc04c481949895ed4512b77fd923"
  },
  {
    "url": "docs/help_doc/basic_plugins/admin_plugins.html",
    "revision": "cdf5159eb7115ac1318edcf2f72ea542"
  },
  {
    "url": "docs/help_doc/basic_plugins/common_plugins.html",
    "revision": "b154a3e639b44903a65993936ed53a46"
  },
  {
    "url": "docs/help_doc/basic_plugins/other_plugins.html",
    "revision": "408c41e7ceb6c989cfb696e84c401061"
  },
  {
    "url": "docs/help_doc/basic_plugins/shop_plugins.html",
    "revision": "9d10125749f07f0bcae400724c9819e3"
  },
  {
    "url": "docs/help_doc/basic_plugins/superuser_plugins.html",
    "revision": "d6b91c94342de8806a5617ac2c1ec9a8"
  },
  {
    "url": "docs/help_doc/configs.html",
    "revision": "3260cc0965f4929900646ef74dab3ddb"
  },
  {
    "url": "docs/help_doc/index.html",
    "revision": "55550e847190dbe3107dc19942bdb72e"
  },
  {
    "url": "docs/help_doc/plugins_index.html",
    "revision": "d4edf043a50f52cb464b459c848c5f68"
  },
  {
    "url": "docs/help_doc/public_plugins/admin_plugins.html",
    "revision": "832292a4321da093a0f2a7a54b7d63de"
  },
  {
    "url": "docs/help_doc/public_plugins/common_plugins/common_plugins.html",
    "revision": "a0f4be5db1a82b81861fee206e8ab5b7"
  },
  {
    "url": "docs/help_doc/public_plugins/draw_card_plugins/draw_card_plugins.html",
    "revision": "405cf29def90a0fb0d3a526dba842d99"
  },
  {
    "url": "docs/help_doc/public_plugins/game_plugins/game_plugins.html",
    "revision": "c7f365fbb02272807de15e40b54fe176"
  },
  {
    "url": "docs/help_doc/public_plugins/genshin_plugins/genshin_plugins.html",
    "revision": "d34cefc5f72ffec51723ea53598468ce"
  },
  {
    "url": "docs/help_doc/public_plugins/other_plugins/other_plugins.html",
    "revision": "fc2c03ea14d91190264204a9b7361982"
  },
  {
    "url": "docs/help_doc/public_plugins/pic_plugins/pic_plugins.html",
    "revision": "f362cb564d8740ccba0df465877296dd"
  },
  {
    "url": "docs/help_doc/public_plugins/superuser_plugins.html",
    "revision": "f78d237c38bdd08d6eab196e013bdae3"
  },
  {
    "url": "docs/help_doc/public_plugins/utils_plugins/utils_plugins.html",
    "revision": "0d99144556809ecf40756f430d6774da"
  },
  {
    "url": "docs/index.html",
    "revision": "9cde9dc6e7add126ee607c70df43e5e4"
  },
  {
    "url": "docs/installation_doc/index.html",
    "revision": "564775d9b0a2545b12983351455fa5b5"
  },
  {
    "url": "docs/installation_doc/install_gocq.html",
    "revision": "20f8563f01edf67033d2e0278436389c"
  },
  {
    "url": "docs/installation_doc/install_webui.html",
    "revision": "dc4a009d80208c547dc9597468ad5b8e"
  },
  {
    "url": "docs/installation_doc/install_zhenxun.html",
    "revision": "8741aa1154abbb2123776d94429db4ce"
  },
  {
    "url": "docs/installation_doc/psql_ubuntu.html",
    "revision": "682c98af02e7e024f2478b82437c46b4"
  },
  {
    "url": "docs/installation_doc/psql_win.html",
    "revision": "5e12b45673fea1a9897e611e3d3cd55c"
  },
  {
    "url": "docs/installation_doc/start_.html",
    "revision": "926f5eafc65b184524f575abe31d7156"
  },
  {
    "url": "docs/update_log/index.html",
    "revision": "079a2bb5b516e3c5492d26a699b3cb8a"
  },
  {
    "url": "gocq/gocq0.png",
    "revision": "9ea372dcebceef63ef360d120c0eb898"
  },
  {
    "url": "gocq/gocq1.png",
    "revision": "4694d1a7821898b8621582f34c20c199"
  },
  {
    "url": "gocq/gocq2.png",
    "revision": "d2cdf4f890af39c5e3789485bb7ad493"
  },
  {
    "url": "gocq/gocq3.png",
    "revision": "9fa7cd2c05babf0a498c17ec950d883c"
  },
  {
    "url": "index.html",
    "revision": "3ea3a875dac5b50b335f46b1094838a9"
  },
  {
    "url": "logo.png",
    "revision": "247217ec9f22445d8f14aedcd1eb1b3f"
  },
  {
    "url": "postgresql/create_1.png",
    "revision": "863be40de0b3454d95edd4b5afbedbd7"
  },
  {
    "url": "postgresql/create_2.png",
    "revision": "a1e3dc7ae8147cf9e9870e68ddb557dd"
  },
  {
    "url": "postgresql/install_1.png",
    "revision": "5777bf4ba4a1a1172182eee657245c61"
  },
  {
    "url": "postgresql/install_2.png",
    "revision": "907ebdd500f2df69237451b10334eff8"
  },
  {
    "url": "postgresql/install_3.png",
    "revision": "59ca7adde67b8e68dcaea233b5252062"
  },
  {
    "url": "postgresql/install_4.png",
    "revision": "9cc4361c9a08e4ade722e3b31270ca0e"
  },
  {
    "url": "postgresql/install_5.png",
    "revision": "9ed0b2ab767eb34068f75e401811ccee"
  },
  {
    "url": "postgresql/install_6.png",
    "revision": "489eb199f1f7df0b383b0d75f9d454bd"
  },
  {
    "url": "postgresql/install_7.png",
    "revision": "7dea74fa82198ea6316e670c6e8e6c83"
  },
  {
    "url": "postgresql/install_8.png",
    "revision": "2abb8fe122be9862cf93ba2d63d51df1"
  },
  {
    "url": "postgresql/setup_1.png",
    "revision": "3a5a246a983d67bb3bfd3225e5c9a263"
  },
  {
    "url": "postgresql/setup_2.png",
    "revision": "30d41b29e3d7dda46ef64cdea8ada87b"
  },
  {
    "url": "postgresql/setup_3.png",
    "revision": "68fbee110da8a9fc50cb87899c8a8779"
  },
  {
    "url": "postgresql/setup_4.png",
    "revision": "ae893884245a94b585d390fe94df7962"
  },
  {
    "url": "postgresql/setup_5.png",
    "revision": "b56415e9112c67a9dc1c1946a1820b5e"
  },
  {
    "url": "tag/index.html",
    "revision": "62adfebae2b3d55b9e1afdd5a3df05cb"
  },
  {
    "url": "timeline/index.html",
    "revision": "d93c2229c9355a816d28df928ef933fe"
  }
].concat(self.__precacheManifest || []);
workbox.precaching.precacheAndRoute(self.__precacheManifest, {});
addEventListener('message', event => {
  const replyPort = event.ports[0]
  const message = event.data
  if (replyPort && message && message.type === 'skip-waiting') {
    event.waitUntil(
      self.skipWaiting().then(
        () => replyPort.postMessage({ error: null }),
        error => replyPort.postMessage({ error })
      )
    )
  }
})
