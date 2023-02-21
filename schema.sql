CREATE TABLE account 
( "account_id" text,
	"created_time" timestamp,
	"created_device" text,
	"created_platform" text,
	"country_code" text,
	"created_app_store_id" int 
);

CREATE TABLE iap_purchase 
( "account_id" text,
	"created_time" timestamp,
	"package_id_hash" text,
	"iap_price_usd_cents" int,
	"app_store_id" int 
);

CREATE TABLE account_date_session 
( "account_id" text,
	"date" date,
	"session_count" int,
	"session_duration_sec" int 
);
