# back-end

## Deployment

### Login AWS: 

```bash
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 943635619664.dkr.ecr.eu-west-3.amazonaws.com
```

### Staging: 
...

### Production: 

```bash
docker build -t crosslink-back:1.0.0 -f deployment/production/backend/Dockerfile . && \
docker tag crosslink-back:1.0.0 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-back:1.0.0 && \
docker push 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-back:1.0.0
```

```bash
docker build -t crosslink-worker:1.0.0 -f deployment/production/worker/Dockerfile . && \
docker tag crosslink-worker:1.0.0 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-worker:1.0.0 && \
docker push 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-worker:1.0.0
```


### Scripts

```bash
ngrok http https://localhost:8000
```


### Widget

```bash
# Connect to Shopify
import shopify
from django.apps import apps

api_version = apps.get_app_config("shopify_app").SHOPIFY_API_VERSION
api_key = apps.get_app_config("shopify_app").SHOPIFY_API_KEY
api_secret_key = apps.get_app_config("shopify_app").SHOPIFY_API_SECRET_KEY

shopify.Session.setup(api_key=api_key, secret=api_secret_key)
shopify_session = shopify.Session(shop.shop_url, api_version)
shopify_session.token = shop.access_token
shopify.ShopifyResource.activate_session(shopify_session)


# get webhooks
import requests
url = f'https://{shop.shop_url}/admin/api/{apps.get_app_config("shopify_app").SHOPIFY_API_VERSION}/webhooks.json'
headers = {
    "X-Shopify-Access-Token": shop.access_token,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.json())
```


### Partitioning products ???
```bash
-- 1. Create parent table
CREATE TABLE products_parent (
    id serial NOT NULL,
    shop_id integer NOT NULL,
    title text,
    description text,
    cms_product_id varchar(20) NOT NULL,
    cms_product_handle text,
    image_url text,
    image_urls text[],
    variant_options jsonb[],
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    PRIMARY KEY (id, shop_id),                
    UNIQUE (cms_product_id, shop_id)         
) PARTITION BY HASH (shop_id);

-- 2. Create 5 child partitions (like ES shards)
CREATE TABLE products_p0 PARTITION OF products_parent
    FOR VALUES WITH (MODULUS 5, REMAINDER 0);
CREATE TABLE products_p1 PARTITION OF products_parent
    FOR VALUES WITH (MODULUS 5, REMAINDER 1);
CREATE TABLE products_p2 PARTITION OF products_parent
    FOR VALUES WITH (MODULUS 5, REMAINDER 2);
CREATE TABLE products_p3 PARTITION OF products_parent
    FOR VALUES WITH (MODULUS 5, REMAINDER 3);
CREATE TABLE products_p4 PARTITION OF products_parent
    FOR VALUES WITH (MODULUS 5, REMAINDER 4);

-- 3. Optional indexes per partition for faster queries
DO $$
BEGIN
    FOR i IN 0..4 LOOP
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_p%s_cms_id ON products_p%s(cms_product_id)', i, i);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_p%s_created_at ON products_p%s(created_at)', i, i);
    END LOOP;
END$$;

-- 4. Move existing data into partitions
INSERT INTO products_parent (id, shop_id, title, description, cms_product_id, cms_product_handle, image_url, image_urls, created_at, updated_at)
SELECT id, shop_id, title, description, cms_product_id, cms_product_handle, image_url, image_urls, created_at, updated_at
FROM products;

-- 4.1. Drop the foreign key constraint
ALTER TABLE variants DROP CONSTRAINT variants_product_id_870dd1c2_fk_products_id;

-- 4.2. Drop the products table
DROP TABLE products;

-- 4.3. Rename partitioned table as products
ALTER TABLE products_parent RENAME TO products;

-- 4.4. Add shop_id to variants
ALTER TABLE variants
    ADD COLUMN shop_id integer;

-- 4.5. Add foreign key constraint
ALTER TABLE variants
    ADD CONSTRAINT variants_product_fk
    FOREIGN KEY (product_id, shop_id) REFERENCES products(id, shop_id);

```

