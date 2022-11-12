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
    "revision": "3a8c98731f38090be8238a7a9b5f21b4"
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
    "url": "assets/js/11.33e2c0fc.js",
    "revision": "966a6376b17e0ffbc38b20dbaedae612"
  },
  {
    "url": "assets/js/12.7ba7ebc6.js",
    "revision": "5804a910d62e383782bf297487e1c480"
  },
  {
    "url": "assets/js/13.95e6493d.js",
    "revision": "fad0c62e87b2e54f3a45be076b736fcd"
  },
  {
    "url": "assets/js/14.c646b8b1.js",
    "revision": "eb912735d3b808cc045f5101c2d5597b"
  },
  {
    "url": "assets/js/15.016b3d5c.js",
    "revision": "74d53741895a161e5df661ddf7ddc2a2"
  },
  {
    "url": "assets/js/16.568aa1e3.js",
    "revision": "a500937a1dfa4b0801fb66d56d43b0a8"
  },
  {
    "url": "assets/js/17.30ebaf3e.js",
    "revision": "ebf0eb77614489a36459bc279dcff6cb"
  },
  {
    "url": "assets/js/18.8f5f3c7b.js",
    "revision": "58df2a6e434a18b780d8679f344809ba"
  },
  {
    "url": "assets/js/19.1bdaca7e.js",
    "revision": "6b531487d7f2cf458646099809b3916f"
  },
  {
    "url": "assets/js/20.5e27a167.js",
    "revision": "33f6cde775ed78030bc602e15fb8675c"
  },
  {
    "url": "assets/js/21.8387030d.js",
    "revision": "9af266ce4d4575eb00fa864dff1f1078"
  },
  {
    "url": "assets/js/22.2b995fc4.js",
    "revision": "e26cb3f8fcf4a2894f0cfebf7c33262e"
  },
  {
    "url": "assets/js/23.9e628ae5.js",
    "revision": "a72616c5071c019a6950ec0fc072d245"
  },
  {
    "url": "assets/js/24.7b09bce7.js",
    "revision": "c44500e738708f7085de713364022fc6"
  },
  {
    "url": "assets/js/25.e6579efb.js",
    "revision": "1c10f0f094e7bed64f316a2251716e04"
  },
  {
    "url": "assets/js/26.1d74e217.js",
    "revision": "ca7f90218cc316449b3f4dcd86a6bf7d"
  },
  {
    "url": "assets/js/27.0a01fa77.js",
    "revision": "81a84f678260363c3201fe69e0e86ef2"
  },
  {
    "url": "assets/js/28.5efe4074.js",
    "revision": "2a7b1c95b11d175a5fc4c655f3142caf"
  },
  {
    "url": "assets/js/29.4aa26b94.js",
    "revision": "53212d8f08482fd2b27e2bb06d56be03"
  },
  {
    "url": "assets/js/3.a9dcdb28.js",
    "revision": "77c3def0358b0b60b343e66acf179866"
  },
  {
    "url": "assets/js/30.40bf902a.js",
    "revision": "8f160d104224607b2a2b05a4a69c7603"
  },
  {
    "url": "assets/js/31.b64c8c2a.js",
    "revision": "5a7595a4601402be0e61dab605d11ffa"
  },
  {
    "url": "assets/js/32.bd6a9d01.js",
    "revision": "4d75d85bf8530bddf5107fd12f47ce1e"
  },
  {
    "url": "assets/js/33.d9b87499.js",
    "revision": "0cf7b8516d34cccdbaf194d01ba93a97"
  },
  {
    "url": "assets/js/34.21d81a5d.js",
    "revision": "1f85bc74fcbbaca96f1ccbd7d8d1881f"
  },
  {
    "url": "assets/js/35.3f961b93.js",
    "revision": "15810717254ebbc52e6da5559324720e"
  },
  {
    "url": "assets/js/36.c9900775.js",
    "revision": "0662449dd58a170e53f9a2361727cf1f"
  },
  {
    "url": "assets/js/37.f84cbc8d.js",
    "revision": "c85f2bb5ff2866651f8f7f49adfc8e5d"
  },
  {
    "url": "assets/js/38.3ac441c7.js",
    "revision": "7897281e0dd256d07f37e9cd5be7d40d"
  },
  {
    "url": "assets/js/39.2f1951f9.js",
    "revision": "3590ae73d82518075399a78134e219c4"
  },
  {
    "url": "assets/js/4.682beda7.js",
    "revision": "9a5feef2c172c481f443669b47150461"
  },
  {
    "url": "assets/js/40.b73ff2e9.js",
    "revision": "d450daf0e8470af252744b8e2af6848e"
  },
  {
    "url": "assets/js/41.64d0bf30.js",
    "revision": "05eef6b27094a99c718184cf6b9ccb40"
  },
  {
    "url": "assets/js/42.dc23b1f4.js",
    "revision": "c0f5e7b4e2565b4d9b6ab23c7ce3d53b"
  },
  {
    "url": "assets/js/43.e4311149.js",
    "revision": "444c0d70df52a8469ac651ffcd614c55"
  },
  {
    "url": "assets/js/44.7cce1867.js",
    "revision": "c10bfa980510d6addca6b60490f65ee8"
  },
  {
    "url": "assets/js/45.8fe5ccce.js",
    "revision": "774bd8533b56f71d2dc9a32ef9dfc4b3"
  },
  {
    "url": "assets/js/46.3ce2888b.js",
    "revision": "0ddf155af1770bd1e4827299120e1374"
  },
  {
    "url": "assets/js/47.42bfeca6.js",
    "revision": "dc8d1c5d032b5944fc19c2cf1428f912"
  },
  {
    "url": "assets/js/48.839a1aed.js",
    "revision": "76768da563fa0d20d1d99974129cbe95"
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
    "url": "assets/js/9.6b86dfe3.js",
    "revision": "dbef90cd54662d6995f47080003be3c5"
  },
  {
    "url": "assets/js/app.bdba9222.js",
    "revision": "51e57fb760c80f78a361abfbc6fbf689"
  },
  {
    "url": "background.png",
    "revision": "f0cb5c6080cc533cce01b7a7182940fe"
  },
  {
    "url": "blogs/about.html",
    "revision": "be22a17a5229d8ecdc9d4102b481f336"
  },
  {
    "url": "categories/index.html",
    "revision": "7363bb84597819281566bb467cec8736"
  },
  {
    "url": "docs/api_doc/group.html",
    "revision": "82e90d5728ea9683a0fbc888969eaf43"
  },
  {
    "url": "docs/api_doc/plugins.html",
    "revision": "0c6daffa099a7adc94e1667b19ad18ed"
  },
  {
    "url": "docs/api_doc/request.html",
    "revision": "19cec9388fe1adb8d81208814313111f"
  },
  {
    "url": "docs/api_doc/system.html",
    "revision": "73de4e7305de81d499c2b29310920928"
  },
  {
    "url": "docs/development_doc/depends.html",
    "revision": "e4e7b924bf8c1bba8ba68016868628fd"
  },
  {
    "url": "docs/development_doc/plugins.html",
    "revision": "0357cb909e3f4d7cb6afe21e006da297"
  },
  {
    "url": "docs/development_doc/shop_handle.html",
    "revision": "a437e6ea51a80b85372d86fdb3528830"
  },
  {
    "url": "docs/development_doc/task_control.html",
    "revision": "ca5389a23f1a22e3dbfa66b7c31f45c6"
  },
  {
    "url": "docs/development_doc/utils.html",
    "revision": "972e83b33cf7ac6e98055259f61f1209"
  },
  {
    "url": "docs/faq/index.html",
    "revision": "b32b741a406b6c496b4c55833a1b92ac"
  },
  {
    "url": "docs/help_doc/basic_plugins/admin_plugins.html",
    "revision": "24fd25ade2c8798033dcf8a5ff905984"
  },
  {
    "url": "docs/help_doc/basic_plugins/common_plugins.html",
    "revision": "16322a1d436ac720c603e407224c99c7"
  },
  {
    "url": "docs/help_doc/basic_plugins/other_plugins.html",
    "revision": "ef30d6563b47a27c8df0ed7535b98a44"
  },
  {
    "url": "docs/help_doc/basic_plugins/shop_plugins.html",
    "revision": "3c98a8b28839a72a58796c4af125e984"
  },
  {
    "url": "docs/help_doc/basic_plugins/superuser_plugins.html",
    "revision": "0b99480ba0d25f0dafeb218dec43cb7f"
  },
  {
    "url": "docs/help_doc/configs.html",
    "revision": "24efdbb0a7526e5df984a55a495448d7"
  },
  {
    "url": "docs/help_doc/index.html",
    "revision": "406f9a2660702e1af90be00ed696cdcd"
  },
  {
    "url": "docs/help_doc/plugins_index.html",
    "revision": "38efe9abafdfc97e6114abd7260e2ae6"
  },
  {
    "url": "docs/help_doc/public_plugins/admin_plugins.html",
    "revision": "b63e3d14070ed25b6d49c4ff7d8da43d"
  },
  {
    "url": "docs/help_doc/public_plugins/common_plugins/common_plugins.html",
    "revision": "30bc7eb51ac8627dcd56be1202ed6045"
  },
  {
    "url": "docs/help_doc/public_plugins/draw_card_plugins/draw_card_plugins.html",
    "revision": "af6fe63e1112912daa68cd3a30e041c1"
  },
  {
    "url": "docs/help_doc/public_plugins/game_plugins/game_plugins.html",
    "revision": "ac73c009842f8a376c1d177b903fd879"
  },
  {
    "url": "docs/help_doc/public_plugins/genshin_plugins/genshin_plugins.html",
    "revision": "3e4c13a423015f7c72fbdd1c1d22fd17"
  },
  {
    "url": "docs/help_doc/public_plugins/other_plugins/other_plugins.html",
    "revision": "374bfce258a60d0dd06fe998d82c7bc6"
  },
  {
    "url": "docs/help_doc/public_plugins/pic_plugins/pic_plugins.html",
    "revision": "467ba9c595020b3e511340a8c1df0525"
  },
  {
    "url": "docs/help_doc/public_plugins/superuser_plugins.html",
    "revision": "cc53757507f1e68453a0e2c797280492"
  },
  {
    "url": "docs/help_doc/public_plugins/utils_plugins/utils_plugins.html",
    "revision": "1d59f0bbb9235bd9f5ece0beb540ca40"
  },
  {
    "url": "docs/index.html",
    "revision": "d0e0e953b4216143389856033c0ef1d6"
  },
  {
    "url": "docs/installation_doc/index.html",
    "revision": "fddd78b26a4ef0679cccfdc15d82c0bd"
  },
  {
    "url": "docs/installation_doc/install_gocq.html",
    "revision": "c44d8b0f2823f378b4d1687fafe6626d"
  },
  {
    "url": "docs/installation_doc/install_postgresql.html",
    "revision": "72b3656be79fca3b2601d27765767608"
  },
  {
    "url": "docs/installation_doc/install_webui.html",
    "revision": "0b5fb57d16e14d61c60ed84657e2773b"
  },
  {
    "url": "docs/installation_doc/install_zhenxun.html",
    "revision": "7c65ec265f0aae636c32cf664755e0e4"
  },
  {
    "url": "docs/installation_doc/start_.html",
    "revision": "3849ebfd6e5750fe340f8bcb936aa189"
  },
  {
    "url": "docs/update_log/index.html",
    "revision": "adafcc2b3fbc9396d24c08b2256a732e"
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
    "url": "index.html",
    "revision": "7b19504e35d8b7016a5cc9741e9b822f"
  },
  {
    "url": "logo.png",
    "revision": "247217ec9f22445d8f14aedcd1eb1b3f"
  },
  {
    "url": "tag/index.html",
    "revision": "45762748e81901d7a96534678af34ccb"
  },
  {
    "url": "timeline/index.html",
    "revision": "f0d2553349c903e9d828c2ff63944945"
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
