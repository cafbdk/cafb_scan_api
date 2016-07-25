from __future__ import unicode_literals

from django.db import models
from datetime import datetime

# choices for nutrient rules (UPGRADE: generate these automagically)

NUTRIENT_CHOICES = [('1','fiber'), ('2','sodium'), ('3','sugar')]
FIELD_CHOICES = [('1','category'), ('2','ingredients'), ('3','name'), ('4','sodium'), ('5','sugar')]
TYPE_CHOICES = [('1','contains'), ('2','first_item'), ('3','lte')]

# Create your models here.
class UPC(models.Model):
	# when nutritional info changes, does the UPC code change? I think we periodically need to ping the API to update this table
	'''
	This records all details from Nutrionix database, or entered manually (functionality TK)
	'''
	upc_code = models.TextField(max_length=50)
	item_name = models.TextField(max_length=100,blank=True,null=True)
	brand_id = models.TextField(max_length=30,blank=True,null=True)
	brand_name = models.TextField(max_length=100,blank=True,null=True)
	item_image = models.TextField(blank=True,null=True)
	item_description = models.TextField(max_length=500,blank=True,null=True)
	api_last_update = models.DateTimeField(default=datetime.now,blank=True,null=True)
	ingredients = models.TextField(max_length=100,blank=True,null=True)
	calories = models.FloatField(blank=True,null=True)
	calories_from_fat = models.FloatField(blank=True,null=True)
	total_fat = models.FloatField(blank=True,null=True)
	saturated_fat = models.FloatField(blank=True,null=True)
	cholesterol = models.FloatField(blank=True,null=True)
	sodium = models.FloatField(blank=True,null=True)
	total_carb = models.FloatField(blank=True,null=True)
	dietary_fiber = models.FloatField(blank=True,null=True)
	sugars = models.FloatField(blank=True,null=True)
	protein = models.FloatField(blank=True,null=True)
	vitamin_a_dv = models.FloatField(blank=True,null=True)
	vitamin_c_dv = models.FloatField(blank=True,null=True)
	calcium_dv = models.FloatField(blank=True,null=True)
	iron_dv = models.FloatField(blank=True,null=True)
	serving_per_cont = models.FloatField(blank=True,null=True)
	serving_size_qty = models.FloatField(blank=True,null=True)
	serving_size_unit = models.TextField(max_length=30,blank=True,null=True)
	data_source = models.TextField(max_length=30,blank=True,null=True)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)


class FoodCat(models.Model):
	'''
	This records all food categories designated in the database
	'''
	load_cat = models.TextField(max_length=3, blank=True, null=True)
	abbr = models.TextField(max_length=10, blank=True, null=True)
	name = models.TextField(max_length=50, blank=True, null=True)
	description = models.TextField(max_length=500, blank=True, null=True)
	notes = models.TextField(max_length=500, blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)


class Scan(models.Model):
	'''
	This records all scans made with the app and what was scanned. (User_id recording TK once we have user auth)
	'''

	upc_id = models.ForeignKey(UPC, on_delete=models.CASCADE, blank=True, null=True)
	upc_raw = models.TextField(max_length=30)
	num_items = models.IntegerField(default='1')
	food_cat_id = models.ForeignKey(FoodCat, on_delete=models.CASCADE, blank=True, null=True)
	device = models.CharField(max_length=15, default='android')
	user_id = models.CharField(max_length=15, default='keyser_soze')
	scan_status = models.TextField(max_length=200, default='Unknown')
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)


class NutRule(models.Model):
	# each rule is store separately, with a timestamp, and the script will take the most recent of each rule, unless a specific time/data are specified ... maybe easier way to do this?
	'''
	This records the set of nutritional guidelines for each type of product
	'''

	food_cat_id = models.ForeignKey(FoodCat, on_delete=models.CASCADE,blank=True, null=True)
	nutrient = models.CharField(choices=NUTRIENT_CHOICES, default='', max_length=100,blank=True, null=True)
	nutritional_field = models.CharField(choices=FIELD_CHOICES, default='', max_length=100,blank=True, null=True)
	rule_type = models.CharField(choices=TYPE_CHOICES, default='', max_length=100,blank=True, null=True)
	value = models.TextField(max_length=20, blank=True, null=True)
	wellness = models.NullBooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)


class WellScore(models.Model):
	'''
	This records the wellness scores and when they were calculated, allowing for a running record of nutrition scores and more flexibility in adjusting nutritional requirements. (i.e., the ability to roll back to previous versions of wellness scores, or look at changes over time)
	It also allows for faster processing for products already in the database.
	'''

	upc_id = models.ForeignKey(UPC, on_delete=models.CASCADE)
	wellness = models.NullBooleanField(default=False,blank=True, null=True)
	nut_id = models.ForeignKey(NutRule, on_delete=models.CASCADE,blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('created',)
