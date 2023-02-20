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
    "revision": "2d2293391343c66d849a385904823360"
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
    "url": "assets/js/12.dcad0bdb.js",
    "revision": "889731cbead067b3c6e35bb78b34edfc"
  },
  {
    "url": "assets/js/13.e4c4fd17.js",
    "revision": "3a6fb4de3db764975cd9657cf03e1ec9"
  },
  {
    "url": "assets/js/14.2830f64c.js",
    "revision": "21595e8efdf248f5eb727af5ef7ad1a4"
  },
  {
    "url": "assets/js/15.fee026ac.js",
    "revision": "09d1035bbdb8f371cf27406d735498ab"
  },
  {
    "url": "assets/js/16.bde6b38b.js",
    "revision": "4bd90a71ea71666044ec65a295e9cf91"
  },
  {
    "url": "assets/js/17.f29f3e31.js",
    "revision": "e8359c5fdcdb9f437629c5436420c35b"
  },
  {
    "url": "assets/js/18.e818a6ac.js",
    "revision": "58ac1d725f4c4625f2ff4737fbf2aa9c"
  },
  {
    "url": "assets/js/19.45b73dcb.js",
    "revision": "d5838b06587b9082b5c1926f12335619"
  },
  {
    "url": "assets/js/20.4da056d2.js",
    "revision": "e52f25e75c0dfb9c8d05a67f73fb839f"
  },
  {
    "url": "assets/js/21.953ab592.js",
    "revision": "b61b4c412cee5570da72c3dbee95301a"
  },
  {
    "url": "assets/js/22.0bdf6c54.js",
    "revision": "291bcb4a4bcfcd2db4007a5adefeee09"
  },
  {
    "url": "assets/js/23.3280fe28.js",
    "revision": "1b3f8cb448767f1e7d2f11cff6f138df"
  },
  {
    "url": "assets/js/24.0a3aa4af.js",
    "revision": "6848ad552d88b2f376caf786ebf15269"
  },
  {
    "url": "assets/js/25.a874b11e.js",
    "revision": "7ea717645211fe3133fcebc09659487a"
  },
  {
    "url": "assets/js/26.ad82a000.js",
    "revision": "bdbaf7da146e04740eeb08325ab9c00d"
  },
  {
    "url": "assets/js/27.f8536418.js",
    "revision": "f5162ec7a3857a990891d0c2d267da18"
  },
  {
    "url": "assets/js/28.99a667cd.js",
    "revision": "059ced03f511fd27136d51228fe6bcc3"
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
    "url": "assets/js/30.45c14c49.js",
    "revision": "3113dc24d953d5b35d1ec57ddf0b7934"
  },
  {
    "url": "assets/js/31.b64c8c2a.js",
    "revision": "5a7595a4601402be0e61dab605d11ffa"
  },
  {
    "url": "assets/js/32.c0c1ea04.js",
    "revision": "392ac354126e5008ebbf040b6db62a05"
  },
  {
    "url": "assets/js/33.0c356f3c.js",
    "revision": "d0232708a3019ce7a4926dba14a85508"
  },
  {
    "url": "assets/js/34.21d81a5d.js",
    "revision": "1f85bc74fcbbaca96f1ccbd7d8d1881f"
  },
  {
    "url": "assets/js/35.c984a944.js",
    "revision": "2b9b69495b15d53b8baaf59287c9d344"
  },
  {
    "url": "assets/js/36.4dc0596a.js",
    "revision": "64781c2966f89f630aedf1e8aabb0504"
  },
  {
    "url": "assets/js/37.e0f88dca.js",
    "revision": "48e7fd76160429dab7bb8c97b62f22b5"
  },
  {
    "url": "assets/js/38.3746fe4a.js",
    "revision": "f8dc2e8c5d3ebb18470bf437e64f7e99"
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
    "url": "assets/js/40.b73ff2e9.js",
    "revision": "d450daf0e8470af252744b8e2af6848e"
  },
  {
    "url": "assets/js/41.a97c74e6.js",
    "revision": "56e27d95c15a772a2759e12995183096"
  },
  {
    "url": "assets/js/42.da549470.js",
    "revision": "0861c7955a20ade5866308aef16d6b50"
  },
  {
    "url": "assets/js/43.ec225ed7.js",
    "revision": "48e3861099614648bf4a5102bf313a69"
  },
  {
    "url": "assets/js/44.fd021a6d.js",
    "revision": "e354ff85b1a3d2ee575e54c270ca3834"
  },
  {
    "url": "assets/js/45.087e2595.js",
    "revision": "9e5c8420998b9d8348aa145ea6c54a01"
  },
  {
    "url": "assets/js/46.0d5eedf6.js",
    "revision": "712d0c4366d9c16bdb6818bacf5c6661"
  },
  {
    "url": "assets/js/47.efc7b6ea.js",
    "revision": "9241db0935dc96331118fc0f894e4591"
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
    "url": "assets/js/app.9a6bfcf8.js",
    "revision": "24a0954bb684165decf03722e1b6f25c"
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
    "revision": "1d49d65918db76b527d24cd32427970a"
  },
  {
    "url": "categories/index.html",
    "revision": "74deeeaef6de4a250a4056a99999f366"
  },
  {
    "url": "docs/api_doc/group.html",
    "revision": "0968672dc274ee276125c4d57ed50996"
  },
  {
    "url": "docs/api_doc/plugins.html",
    "revision": "d928392c8d6d502b6ff9d46be360a9fd"
  },
  {
    "url": "docs/api_doc/request.html",
    "revision": "3ddd290798495cd3a22ac7e58cc74436"
  },
  {
    "url": "docs/api_doc/system.html",
    "revision": "cdc8a6640889ff8c05cb0836a4a5aef4"
  },
  {
    "url": "docs/development_doc/depends.html",
    "revision": "a0ff48c4e1c5dedcb9c463353bc9a11a"
  },
  {
    "url": "docs/development_doc/plugins.html",
    "revision": "4370d07a7edcbcdfa84a52cb43e18340"
  },
  {
    "url": "docs/development_doc/shop_handle.html",
    "revision": "1996a53afc8cc9e15d8438a718f5e941"
  },
  {
    "url": "docs/development_doc/task_control.html",
    "revision": "e985df58c382aebe8304809f9f60f3f4"
  },
  {
    "url": "docs/development_doc/utils.html",
    "revision": "1aa23faafabb7ab2344d306d03dc36c4"
  },
  {
    "url": "docs/faq/index.html",
    "revision": "5a21d299a722e81792ab26630276a4f3"
  },
  {
    "url": "docs/help_doc/basic_plugins/admin_plugins.html",
    "revision": "b214fd1b3d6848eda51333920df96b6c"
  },
  {
    "url": "docs/help_doc/basic_plugins/common_plugins.html",
    "revision": "098973840619f984fc66648b5bd167f7"
  },
  {
    "url": "docs/help_doc/basic_plugins/other_plugins.html",
    "revision": "37324c4c42b424b6f798a3922de9a62d"
  },
  {
    "url": "docs/help_doc/basic_plugins/shop_plugins.html",
    "revision": "4d6460899ad9c36111676d8dba2d234c"
  },
  {
    "url": "docs/help_doc/basic_plugins/superuser_plugins.html",
    "revision": "4e6d58f332ba37a41fc077765e32213f"
  },
  {
    "url": "docs/help_doc/configs.html",
    "revision": "f8c10a333537db8c999af3fb49f87da2"
  },
  {
    "url": "docs/help_doc/index.html",
    "revision": "308cb24f72c83b0591d4f12ae0082a6a"
  },
  {
    "url": "docs/help_doc/plugins_index.html",
    "revision": "9025e8dac3ba95d32a98521f4af6606b"
  },
  {
    "url": "docs/help_doc/public_plugins/admin_plugins.html",
    "revision": "d06e0902aeabb5040446adbf18b8fc93"
  },
  {
    "url": "docs/help_doc/public_plugins/common_plugins/common_plugins.html",
    "revision": "0c16345b71ff427ceb7ef0627cb90b21"
  },
  {
    "url": "docs/help_doc/public_plugins/draw_card_plugins/draw_card_plugins.html",
    "revision": "e855a6ba1cce3f3709efd13e5cf58612"
  },
  {
    "url": "docs/help_doc/public_plugins/game_plugins/game_plugins.html",
    "revision": "b658f999896837f861a48c4ed99d0e55"
  },
  {
    "url": "docs/help_doc/public_plugins/genshin_plugins/genshin_plugins.html",
    "revision": "d7b78f027439be1d609ce6fe2f95d932"
  },
  {
    "url": "docs/help_doc/public_plugins/other_plugins/other_plugins.html",
    "revision": "aa07e7857c4a814896b29df56e9549ff"
  },
  {
    "url": "docs/help_doc/public_plugins/pic_plugins/pic_plugins.html",
    "revision": "38edd7130625b777f19b3d1debf21ba7"
  },
  {
    "url": "docs/help_doc/public_plugins/superuser_plugins.html",
    "revision": "f9672112ec8566ad85bdffdc9af44f4c"
  },
  {
    "url": "docs/help_doc/public_plugins/utils_plugins/utils_plugins.html",
    "revision": "a10c0718aabc13315193417e1a475621"
  },
  {
    "url": "docs/index.html",
    "revision": "384bb6531899d9e0cf7d2c44d9465eb1"
  },
  {
    "url": "docs/installation_doc/index.html",
    "revision": "e79e41c533fb0bb4c9001db16e0e5dc6"
  },
  {
    "url": "docs/installation_doc/install_gocq.html",
    "revision": "e8b181a2270daa36b02eb67951e3a0a4"
  },
  {
    "url": "docs/installation_doc/install_webui.html",
    "revision": "ec2a069ea798a84117d0a53b36cc4710"
  },
  {
    "url": "docs/installation_doc/install_zhenxun.html",
    "revision": "9da6e485bbb00dadac6b45f5bf4fdedf"
  },
  {
    "url": "docs/installation_doc/psql_ubuntu.html",
    "revision": "bd78909045aa825d35aa127781f94303"
  },
  {
    "url": "docs/installation_doc/psql_win.html",
    "revision": "8498c216b757b228b6b1a16b80b876af"
  },
  {
    "url": "docs/installation_doc/start_.html",
    "revision": "46a95966df74f4a33918566373221487"
  },
  {
    "url": "docs/update_log/index.html",
    "revision": "fda6d898c3849f27d6f0c15e7fe0359c"
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
    "revision": "933613d4311a9271a36aa167ac67c258"
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
    "revision": "f712eaa2fa270d3056210bdee6d5f025"
  },
  {
    "url": "timeline/index.html",
    "revision": "ef772281ab28288106f6e070b6bfdbe7"
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
