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
    "revision": "1813c7cc5dd631f2a9678c0cafd4c035"
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
    "url": "assets/js/13.7fc2706d.js",
    "revision": "953ac90d04cad0cbab995b8e446b23a8"
  },
  {
    "url": "assets/js/14.ebcddac7.js",
    "revision": "a0e54e6a8ccda594b67f2ba8c5f1e525"
  },
  {
    "url": "assets/js/15.016b3d5c.js",
    "revision": "74d53741895a161e5df661ddf7ddc2a2"
  },
  {
    "url": "assets/js/16.bf4145e4.js",
    "revision": "b710d41e358b55e65f349f6e55ee4aa8"
  },
  {
    "url": "assets/js/17.b1a47a17.js",
    "revision": "4a4b0140846bd168cfd8c7a75fd9aaa4"
  },
  {
    "url": "assets/js/18.318408c6.js",
    "revision": "415f8a81b1be31b22d6e65ec83f0906a"
  },
  {
    "url": "assets/js/19.c9f09981.js",
    "revision": "94e7b7094e3f6ea90a871ee6aecccc6e"
  },
  {
    "url": "assets/js/20.5e27a167.js",
    "revision": "33f6cde775ed78030bc602e15fb8675c"
  },
  {
    "url": "assets/js/21.ee135803.js",
    "revision": "a3abd8e2797deac5a67aec9e47dfb1ff"
  },
  {
    "url": "assets/js/22.2b995fc4.js",
    "revision": "e26cb3f8fcf4a2894f0cfebf7c33262e"
  },
  {
    "url": "assets/js/23.242d55bc.js",
    "revision": "75df2ff741059fce4372381260416292"
  },
  {
    "url": "assets/js/24.9f27d9b8.js",
    "revision": "1548397b3318fd360d1b2b22d8df2d7f"
  },
  {
    "url": "assets/js/25.692f68e1.js",
    "revision": "4b5ab4fc353527a8afc1fe0b0d924938"
  },
  {
    "url": "assets/js/26.ad82a000.js",
    "revision": "bdbaf7da146e04740eeb08325ab9c00d"
  },
  {
    "url": "assets/js/27.5138d424.js",
    "revision": "0d591170007be39d0faf137c8a1a2f51"
  },
  {
    "url": "assets/js/28.34d807e2.js",
    "revision": "5ef0bc25c6fa8eeb0e85f313d55e1ace"
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
    "url": "assets/js/40.d7de8f2a.js",
    "revision": "b5f78048917922b0c1fe1a784d551895"
  },
  {
    "url": "assets/js/41.f61732a0.js",
    "revision": "bd4852b66d6d8667ab44618f78b21426"
  },
  {
    "url": "assets/js/42.43218fc5.js",
    "revision": "34415ecd3a7394569844bd400babd9af"
  },
  {
    "url": "assets/js/43.59150fa9.js",
    "revision": "d092204e3782521a1affd5b709d54ee3"
  },
  {
    "url": "assets/js/44.043eafce.js",
    "revision": "2d87c2a28759759449e5eb94948defe3"
  },
  {
    "url": "assets/js/45.45bcadfd.js",
    "revision": "485e26e5b6761e2e012eb56a8699c90b"
  },
  {
    "url": "assets/js/46.b29ca1e0.js",
    "revision": "68708f298859858f8988840d53326f50"
  },
  {
    "url": "assets/js/47.d5cb57d5.js",
    "revision": "5ff24d4b10e94da8f7e9a996d7cb4da6"
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
    "url": "assets/js/app.bc6de04c.js",
    "revision": "1a0902dbf883598546171d5321be2788"
  },
  {
    "url": "background.png",
    "revision": "f0cb5c6080cc533cce01b7a7182940fe"
  },
  {
    "url": "blogs/about.html",
    "revision": "9c4275eaf03e9eba23730237ad2e1a5f"
  },
  {
    "url": "categories/index.html",
    "revision": "5e422841d0dccbc7d6b3c94cbddc43d2"
  },
  {
    "url": "docs/api_doc/group.html",
    "revision": "0a0305cd39fbd1f982c53398436f23ef"
  },
  {
    "url": "docs/api_doc/plugins.html",
    "revision": "33687b9050ecd65eab31b755ecdb4e43"
  },
  {
    "url": "docs/api_doc/request.html",
    "revision": "f73080a2dfb52b19909733d85634d69a"
  },
  {
    "url": "docs/api_doc/system.html",
    "revision": "52786d0390d25b33481f9692e96c1e4f"
  },
  {
    "url": "docs/development_doc/depends.html",
    "revision": "4846ede5c9c64fe6bd6f677ec258743b"
  },
  {
    "url": "docs/development_doc/plugins.html",
    "revision": "9e5d94bcb5a752fecb43422534eb9d7a"
  },
  {
    "url": "docs/development_doc/shop_handle.html",
    "revision": "e4de6edaf69d9d508299d87f7163c65e"
  },
  {
    "url": "docs/development_doc/task_control.html",
    "revision": "749244a46efcf2748dde5b3aa0e73965"
  },
  {
    "url": "docs/development_doc/utils.html",
    "revision": "bbb6cffe795f1a2ff9d72af0e20d47b9"
  },
  {
    "url": "docs/faq/index.html",
    "revision": "b2559baf2da0899d285673ccb33cdb4a"
  },
  {
    "url": "docs/help_doc/basic_plugins/admin_plugins.html",
    "revision": "43b63cc68d810c0c37419071a8190c1b"
  },
  {
    "url": "docs/help_doc/basic_plugins/common_plugins.html",
    "revision": "5810dfb01a847f8be69b18e17aa9e626"
  },
  {
    "url": "docs/help_doc/basic_plugins/other_plugins.html",
    "revision": "2c3c689ac1a9b4eebe6b2297858701c7"
  },
  {
    "url": "docs/help_doc/basic_plugins/shop_plugins.html",
    "revision": "b41f8f9260b82d72de9e52e0cc31c684"
  },
  {
    "url": "docs/help_doc/basic_plugins/superuser_plugins.html",
    "revision": "7c9b77c86b43d10b9fee9e949cbbb5c7"
  },
  {
    "url": "docs/help_doc/configs.html",
    "revision": "d3475d187773244859f9fa078b8e6d0c"
  },
  {
    "url": "docs/help_doc/index.html",
    "revision": "5eceb0baf25c3aba990753b704d5fa46"
  },
  {
    "url": "docs/help_doc/plugins_index.html",
    "revision": "a35b48f81d30f434c0786c4bddd2d320"
  },
  {
    "url": "docs/help_doc/public_plugins/admin_plugins.html",
    "revision": "d5e682159068dbea6e6d84e893be81c1"
  },
  {
    "url": "docs/help_doc/public_plugins/common_plugins/common_plugins.html",
    "revision": "c4e3c841e37fb759e0d56ae2557b936f"
  },
  {
    "url": "docs/help_doc/public_plugins/draw_card_plugins/draw_card_plugins.html",
    "revision": "82b894b587fade3a39a0056fbef6e81a"
  },
  {
    "url": "docs/help_doc/public_plugins/game_plugins/game_plugins.html",
    "revision": "f5ce64cc894ce182e4b8f1dc30aee179"
  },
  {
    "url": "docs/help_doc/public_plugins/genshin_plugins/genshin_plugins.html",
    "revision": "6e890c70756e953030a19ad390c268cb"
  },
  {
    "url": "docs/help_doc/public_plugins/other_plugins/other_plugins.html",
    "revision": "235dc533c44e4d539e1ce2dfbb596745"
  },
  {
    "url": "docs/help_doc/public_plugins/pic_plugins/pic_plugins.html",
    "revision": "623d5cd24e5d9d6d7ddd9f70ab7cc3bc"
  },
  {
    "url": "docs/help_doc/public_plugins/superuser_plugins.html",
    "revision": "c4463286930cea211456e11ad1a7acde"
  },
  {
    "url": "docs/help_doc/public_plugins/utils_plugins/utils_plugins.html",
    "revision": "f98183ddf8a61efe21aa58cbf72ddabb"
  },
  {
    "url": "docs/index.html",
    "revision": "ab21ad808e1a500d2e708ffda9921327"
  },
  {
    "url": "docs/installation_doc/index.html",
    "revision": "20aae155ea6079db980ca43e45a3d718"
  },
  {
    "url": "docs/installation_doc/install_gocq.html",
    "revision": "bdbbcef7ee0696627b65bf04711816fa"
  },
  {
    "url": "docs/installation_doc/install_postgresql.html",
    "revision": "35ae32f6288e41217a4dff162419a421"
  },
  {
    "url": "docs/installation_doc/install_webui.html",
    "revision": "677824f75a9194bbc2aa182fd8c2f625"
  },
  {
    "url": "docs/installation_doc/install_zhenxun.html",
    "revision": "fad61a60debc47f08e9de3f306996687"
  },
  {
    "url": "docs/installation_doc/start_.html",
    "revision": "78ddaaff598d8cca3a3d43fc00cb5c4a"
  },
  {
    "url": "docs/update_log/index.html",
    "revision": "105fffa978e669ded2ace626fdcab796"
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
    "revision": "81eb1cbcecef841bf90c61e836b2a1a0"
  },
  {
    "url": "logo.png",
    "revision": "247217ec9f22445d8f14aedcd1eb1b3f"
  },
  {
    "url": "tag/index.html",
    "revision": "6bfdecef1bc35b2fbffe20da23a7d06c"
  },
  {
    "url": "timeline/index.html",
    "revision": "7aa53f75dbb2c053129f88f47fc05fc9"
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
