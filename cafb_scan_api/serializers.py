from rest_framework import serializers
from cafb_scan_api.models import UPC, Scan, FoodCat, WellScore, NutRule

class UPCSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = UPC
		fields = ('upc_code', 'item_name', 'brand_id', 'brand_name', 'item_image', 'item_description', 'api_last_update', 'ingredients', 'calories', 'calories_from_fat', 'total_fat', 'saturated_fat', 'cholesterol', 'sodium', 'total_carb', 'dietary_fiber', 'sugars', 'protein', 'vitamin_a_dv', 'vitamin_c_dv', 'calcium_dv', 'iron_dv', 'serving_per_cont', 'serving_size_qty', 'serving_size_unit', 'created')       


class ScanSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Scan
		fields = ('upc_id', 'upc_raw', 'num_items', 'created', 'food_cat_id', 'device', 'user_id', 'scan_status')


class FoodCatSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = FoodCat
		fields = ('load_cat', 'abbr', 'name', 'description', 'notes', 'created')


class WellScoreSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = WellScore
		fields = ('upc_id', 'wellness', 'nut_id', 'created')


class NutRuleSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = NutRule
		fields = ('food_cat_id', 'nutrient', 'nutritional_field', 'rule_type', 'value', 'wellness', 'created')