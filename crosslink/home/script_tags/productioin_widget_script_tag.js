(function() {
  const url = "https://crosslink.fr/api/shopify/cross-sell-widget";
  var prodWidgetApi = {
    Start: function() {
      //Get the *.myshopify.com domain
      var shop = Shopify.shop;

      //Load the store owner's widget settings
      var params = {
        shop: shop,
        page_url: window.location,
      };
      if (typeof Shopify.checkout !== "undefined") {
        Shopify.checkout.created_at &&
          (params.checkout_created_at = Shopify.checkout.created_at);
        Shopify.checkout.customer_id &&
          (params.checkout_customer_id = Shopify.checkout.customer_id);
        Shopify.checkout.email &&
          (params.checkout_customer_email = Shopify.checkout.email);
        Shopify.checkout.id && (params.checkout_id = Shopify.checkout.id);
        Shopify.checkout.name && (params.checkout_name = Shopify.checkout.name);
        Shopify.checkout.order_id &&
          (params.checkout_order_id = Shopify.checkout.order_id);
        Shopify.checkout.token &&
          (params.checkout_token = Shopify.checkout.token);
        Shopify.checkout.shipping_address.first_name &&
          (params.checkout_shipping_address_first_name =
            Shopify.checkout.shipping_address.first_name);
        Shopify.checkout.shipping_address.last_name &&
          (params.checkout_shipping_address_last_name =
            Shopify.checkout.shipping_address.last_name);
        Shopify.checkout.line_items &&
          (params.variant_ids = Shopify.checkout.line_items.map(item => item.variant_id).toString());
        Shopify.checkout.line_items &&
          (params.product_ids = Shopify.checkout.line_items.map(item => item.product_id).toString());
        Shopify.checkout.line_items &&
          (params.quantities = Shopify.checkout.line_items.map(item => item.quantity).toString());
        Shopify.checkout.line_items &&
          (params.total_prices = Shopify.checkout.line_items.map(item => {
            let discountAmount = 0;
            item.discount_allocations.forEach((discount) => discountAmount += discount.amount);
            const totalPrice = Number(item.line_price) - Number(discountAmount);
            return totalPrice.toFixed(2);
          }).toString());
      }

      if (typeof Shopify.Checkout !== "undefined") {
        Shopify.Checkout.token &&
          (params.checkout_token = Shopify.Checkout.token);
      }

      prodWidgetApi.LoadWidget(params, function(widgetHtml) {
        var fragment = document.createDocumentFragment();
        var div = document.createElement("div");
        div.innerHTML = widgetHtml.trim();
        var widgetNodes = div.childNodes;
        for (var i = 0; i < widgetNodes.length; i++) {
          var node = widgetNodes[i];
          fragment.appendChild(node);
        }
        var boxes = document.querySelectorAll(".content-box");
        var titleBox = null;
        for (var i = 0; i < boxes.length; i++) {
          if (boxes[i].querySelector(".os-step__title")) {
            titleBox = boxes[i];
            break;
          }
        }

        if (titleBox) {
          titleBox.parentElement.insertBefore(fragment, titleBox.nextSibling);
        }

        function setCrossLinkSectionWidth() {
          document.getElementById("crosslink-section-production")
            .style.width = (document.getElementsByClassName('content-box')[0].getBoundingClientRect()
              .width - 32) + "px"
        }
        setCrossLinkSectionWidth();
        window.addEventListener('resize', setCrossLinkSectionWidth);
        
        if (document.getElementById('crosslink-splide-1')){
          var splide1 = new Splide('#crosslink-splide-1', {
            'arrows': false,
            'keyboard': false,
            'pagination': false,
            'type': 'loop',
            'perPage': 3,
            'perMove': 1,
            'autoplay': true,
            'interval': 3000,
            'autoWidth': 'true',
            'gap': '8px',
            'breakpoints': {
              '480': {
                'perPage': 2,
              },
            }
          })
          var bar1 = splide1.root.querySelector('.my-carousel-progress-bar-1');
          // Updates the bar width whenever the carousel moves:
          splide1.on('mounted move', function() {
            var end = splide1.Components.Controller.getEnd() + 1;
            var rate = Math.min((splide1.index + 1) / end, 1);
            bar1.style.width = String(100 * rate) + '%';
          });
          splide1.mount();
        };

        if (document.getElementById('crosslink-splide-2')){
          var splide2 = new Splide('#crosslink-splide-2', {
            'arrows': false,
            'keyboard': false,
            'pagination': false,
            'type': 'loop',
            'perPage': 3,
            'perMove': 1,
            'autoplay': true,
            'interval': 3000,
            'autoWidth': 'true',
            'gap': '8px',
            'breakpoints': {
              '480': {
                'perPage': 2,
              },
            }
          })
          var bar2 = splide2.root.querySelector('.my-carousel-progress-bar-2');
          // Updates the bar width whenever the carousel moves:
          splide2.on('mounted move', function() {
            var end = splide2.Components.Controller.getEnd() + 1;
            var rate = Math.min((splide2.index + 1) / end, 1);
            bar2.style.width = String(100 * rate) + '%';
          });
          splide2.mount();
        };
      });
    },
    ExecuteJSONP: function(url, parameters, callback) {
      //Prepare a function name that will be called when the JSONP request has loaded.
      //It should be unique, to prevent accidentally calling it multiple times.
      var callbackName = "MyAppJSONPCallback" + new Date()
        .getMilliseconds();

      //Make the callback function available to the global scope,
      //otherwise it can't be called when the settings are loaded.
      window[callbackName] = callback;

      //Convert the parameters into a querystring
      var kvps = ["jsonp=" + callbackName];
      var keys = Object.getOwnPropertyNames(parameters);

      for (var i = 0; i < keys.length; i++) {
        var key = keys[i];

        kvps.push(key + "=" + encodeURIComponent(parameters[key]));
      }

      //Add a unique parameter to the querystring, to overcome browser caching.
      kvps.push("uid=" + new Date()
        .getMilliseconds());

      var qs = "?" + kvps.join("&");

      //Build the script element, passing along the shop name and the load function's name
      var script = document.createElement("script");
      script.src = url + qs;
      script.async = true;
      script.type = "text/javascript";

      //Append the script to the document's head to execute it.
      document.head.appendChild(script);
    },
    LoadWidget: function(params, callback) {
      //Prepare a function to handle when the settings are loaded.
      var loadWidget = function(widget) {
        //Return the settings to the Start function so it can continue loading.
        callback(widget);
      };

      //Get the settings
      prodWidgetApi.ExecuteJSONP(url, params, loadWidget);
    },
  };

  //Start the widget
  prodWidgetApi.Start();

  //Optionally make the api available to the global scope for debugging.
  window["MyWidget"] = prodWidgetApi;
})();
