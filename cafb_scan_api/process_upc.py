from django.core.exceptions import ObjectDoesNotExist
import os
import unirest
import pprint
from cafb_scan_api.models import UPC, Scan, FoodCat, WellScore, NutRule

class Food(object):
	'''
	This class will cover the lifecycle from when an item's UPC code is scanned to the return of a wellness designation (Yes, No, Unknown).

	An item in the Food class will be intiated with a UPC code and food category ID, returned via the scanner app. This class contains the functions needed to ping Nutrionix for nutrition info, enter nutrition info by hand, and calculate wellness.

	The process will cover three scenarios:
		-1. Wellness score calculated previously (yay!)
			-Score returned. The End.
		-2. Wellness score not calculated
			-3a. Item can be obtained via OFF or Nutrionix API
				-Nutrition info on item added to UPC table
				-Wellness score calculated; stored in WellScore table and returned to user.
			-3b. Item not available via APIs
				-User pinged to enter information

		3b folo if user can enter info: This triggers a POST request, this time with info entered via form:            
			-Info stored in UPC table
			-Wellness score calculated; stored in WellScore table and returned to user

		This will require a Nutrionix API key and ID, which can be found here: https://developer.nutritionix.com/
		OFF does not require API key
	'''


	def __init__(self, upc_code, food_cat, api_key, api_id):
		self.upc_code = upc_code
		self.api_key = api_key 
		self.api_id = api_id
		self.food_cat = food_cat
		self.food_info, self.api_response, self.wellness = self.run()
		
	def reset_keys(self, new_key):
		"""
		Change API keys
		"""
		setattr(self, 'api_key', new_key)
		
	def reset_id(self, new_id):
		"""
		Change API id
		"""
		setattr(self, 'api_id', new_id)
	

	def check_wellness(self):
		'''
		This checks for an existing wellness score based on the upc code and nutrition rule for the given food category.
		Returns wellness score if exists, false otherwise.
		'''
		try:
			upc_key = UPC.objects.values_list('pk',flat=True).get(upc_code=self.upc_code)
			cat_key = FoodCat.objects.values_list('pk', flat=True).get(load_cat=self.food_cat)
			nut_key = NutRule.objects.values_list('pk', flat=True).get(food_cat_id_id=cat_key)
			return WellScore.objects.filter(upc_id_id=upc_key,nut_id_id=nut_key).values()
		except ObjectDoesNotExist:
			return False


	def get_food_item(self):
		"""
		Get nutritional info from the UPC table, Nutrionix API, or add in new item if not found
		"""

		#check if in our database already
		db_check = UPC.objects.filter(upc_code=self.upc_code).values()
		if db_check:
			self.food_info = db_check[0]
			self.api_response = {'success' : 'Already in database'}
		else:
			#first try OFF 'cause it's free, otherwise try nutritionix
			off_check = self.get_open_food_facts()
			self.food_info, source = (off_check, 'OFF') if off_check else (self.get_nutrionix(), 'Nutrionix')

			api_success = {'success' : 'Item found in {0}'.format(source)}
			api_fail = {'error': 'API Error or Item Not Found. Please enter item details via app.'}
			self.api_response =  api_success if self.food_info else api_fail

		return self.food_info, self.api_response

	def get_open_food_facts(self):
		response = unirest.get("http://world.openfoodfacts.org/api/v0/product/{upc}.json".format(upc=self.upc_code),headers={"Accept": "application/json"})

		if response.code == 200 and response.body['status'] == 1:
			self.food_info = response.body['product']
			self.food_info['ingredients'] = ", ".join([item['text'] for item in self.food_info['ingredients']])
			#converting their pretty list of dictionaries to a plain ole list of ingredients so it is comparable to the other API

			#ISSUE: Please check my work
			obj = UPC(
					upc_code=self.upc_code,
					item_name=self.food_info['product_name'],
					brand_id=None, #not in OFF
					brand_name=self.food_info['brands'],
					item_description=self.food_info['generic_name'],
					api_last_update=self.food_info['last_edit_dates_tags'][0],
					ingredients=self.food_info['ingredients'],
					#RE: nutriMents: yes there's a typo in the key; not sure how long they'll keep it; if this starts fussing that might be something to check out first
					calories=float(self.food_info['nutriments']['energy'])**1000 if self.food_info['nutriments']['energy'] and self.food_info['nutriments']['energy_unit'] == 'kcal' else None,
					#ISSUE: There are a bunch of wacky foreign units in OFF; need to write fxn to get all these to calories in the US sense
					calories_from_fat=None, #NA in OFF, as far as I can tell
					total_fat=float(self.food_info['nutriments']['fat']) if self.food_info['nutriments']['fat'] else None,
					saturated_fat=float(self.food_info['nutriments']['saturated-fat']) if self.food_info['nutriments']['saturated-fat'] else None,
					cholesterol=None, #NA in OFF, as far as I can tell
					sodium=float(self.food_info['nutriments']['sodium']) if self.food_info['nutriments']['sodium'] else None,
					total_carb=float(self.food_info['nutriments']['carbohydrates']) if self.food_info['nutriments']['carbohydrates'] else None,
					dietary_fiber=float(self.food_info['nutriments']['fiber']) if self.food_info['nutriments']['fiber'] else None,
					sugars=float(self.food_info['nutriments']['sugars']) if self.food_info['nutriments']['sugars'] else None,
					protein=float(self.food_info['nutriments']['proteins']) if self.food_info['nutriments']['proteins'] else None,
					vitamin_a_dv=None, #NA in OFF, as far as I can tell
					vitamin_c_dv=None, #NA in OFF, as far as I can tell
					calcium_dv=None, #NA in OFF, as far as I can tell
					iron_dv=None, #NA in OFF, as far as I can tell
					serving_per_cont=float(self.food_info['nutriments']['fat']) if self.food_info['nutriments']['fat'] else None,
					serving_size_qty=float(self.food_info['serving_quantity']) if self.food_info['serving_quantity'] else None,
					serving_size_unit=filter(lambda x: x.isalpha(), self.food_info['serving_size']),
					data_source='Open Food Facts'
			)

			obj.save()
			self.food_info = UPC.objects.filter(upc_code=self.upc_code).values()[0] 
			#ISSUE: better parsing of OFF (kind of a hot mess), this was very rushed; hence why I am just using what I put in table

			return self.food_info

	def get_nutrionix(self):
		response = unirest.get("https://api.nutritionix.com/v1_1/item?upc={upc}&appId={apiID}&appKey={apiKey}".format(
		apiID=self.api_id, apiKey=self.api_key,upc=self.upc_code),headers={"Accept": "application/json"})

		if response.code == 200:
			self.food_info = response.body
			new_dict_keys = map(lambda x:str(x).replace('nf_',''), self.food_info.keys())
			new_dict_keys = ['ingredients' if name=='ingredient_statement' else name for name in new_dict_keys]
			self.food_info = dict(zip(new_dict_keys,self.food_info.values()))

			obj = UPC(
					upc_code=self.upc_code,
					item_name=self.food_info['item_name'],
					brand_id=self.food_info['brand_id'],
					brand_name=self.food_info['brand_name'],
					item_description=self.food_info['item_description'],
					api_last_update=self.food_info['updated_at'],
					ingredients=self.food_info['ingredients'],
					calories=float(self.food_info['calories']) if self.food_info['calories'] else None,
					#ISSUE: All of the ones below this point should be rewritten to be like the one above. Basically, the data comes from the API as a string, and we need it to be float or None, but float has a problem with Nones, so here we are. Also possible that the API call data comes in as float, but it felt like an issue at the time.
					calories_from_fat=None if not self.food_info['calories_from_fat'] else float(self.food_info['calories_from_fat']),
					total_fat=None if not self.food_info['total_fat'] else float(self.food_info['total_fat']),
					saturated_fat=None if not self.food_info['saturated_fat'] else float(self.food_info['saturated_fat']),
					cholesterol=None if not self.food_info['cholesterol'] else float(self.food_info['cholesterol']),
					sodium=None if not self.food_info['sodium'] else float(self.food_info['sodium']),
					total_carb=None if not self.food_info['total_carbohydrate'] else float(self.food_info['total_carbohydrate']),
					dietary_fiber=None if not self.food_info['dietary_fiber'] else float(self.food_info['dietary_fiber']),
					sugars=None if not self.food_info['sugars'] else float(self.food_info['sugars']),
					protein=None if not self.food_info['protein'] else float(self.food_info['protein']),
					vitamin_a_dv=None if not self.food_info['vitamin_a_dv'] else float(self.food_info['vitamin_a_dv']),
					vitamin_c_dv=None if not self.food_info['vitamin_c_dv'] else float(self.food_info['vitamin_c_dv']),
					calcium_dv=None if not self.food_info['calcium_dv'] else float(self.food_info['calcium_dv']),
					iron_dv=None if not self.food_info['iron_dv'] else float(self.food_info['iron_dv']),
					serving_per_cont=None if not self.food_info['servings_per_container'] else float(self.food_info['servings_per_container']),
					serving_size_qty=None if not self.food_info['serving_size_qty'] else float(self.food_info['serving_size_qty']),
					serving_size_unit=self.food_info['serving_size_unit'],
					data_source='Nutrionix'
			)

			obj.save()

			return self.food_info
	


	def add_new_food_item(self):
		"""
		Add new food item, via info sent via post from app. Feature TK.

		This process should also traverse the Scan table and link all previous occurences (probably only once) of the UPC code to the PK of that code in the UPC database. What comes from the scanner is stored in the upc_raw column in the Scan table.
		"""
		pass
  
		
	def convert_dict_to_attributes(self):
		"""
		Convert the keys in the dictionary to object attributes
		"""
		for key, value in self.food_info:
			setattr(self, key, value)
	
	#ISSUE: These three fxns could probably be cleaned up by someone who is better at decorators	
	@property
	def main_ingredient(self):
		"""
		Extract main ingredient of the food
		"""
		self.food_info['ingredients'] = self.food_info['ingredients'].replace('+++', ',')
		return self.food_info['ingredients'].split(',')[0]
	
	def set_food_info(self, nutrition, value):
		"""
		Change the nutrtion value of food
		"""
		pass
		#setattr(self, nutrition, value)

	def get_nut_rule(self):
		cat_key = FoodCat.objects.values_list('pk', flat=True).get(load_cat=self.food_cat)
		return NutRule.objects.filter(food_cat_id_id=cat_key).values()[0]

	def wellness_logic(self):
		'''
		This functions fetches applicable nutrition rule, then applies it to food. The result is returned to user and stored in WellScore table.
		'''
		nut_rule = self.get_nut_rule()
		self.food_info['category'] = str(self.food_cat)

		#ISSUE: Refactor this into multiple, more modular functions because this makes me sad
		if nut_rule['rule_type'] == 'contains':
			if nut_rule['value'].lower() in self.food_info[nut_rule['nutritional_field']].lower():
				self.wellness = nut_rule['wellness']
			else:
				self.wellness = abs(nut_rule['wellness'] - 1)
		elif nut_rule['rule_type'] == 'lte':
			if float(self.food_info[nut_rule['nutritional_field']]) <= float(nut_rule['value']):
				self.wellness = nut_rule['wellness']
			else:
				self.wellness = abs(nut_rule['wellness'] - 1)
		elif nut_rule['rule_type'] == 'first_item':
			if nut_rule['value'].lower() in self.main_ingredient:
				self.wellness = nut_rule['wellness']
			else:
				self.wellness = abs(nut_rule['wellness'] - 1)
		else:
			self.wellness = 0 #ISSUE: update data model to support 'Unknown' or 'None' choice

		upc_key = UPC.objects.values_list('pk',flat=True).get(upc_code=self.upc_code)
		obj = WellScore(upc_id_id=upc_key, nut_id_id=nut_rule['id'],wellness=self.wellness) 
		obj.save()

		return self.wellness
		
	def run(self):
		if self.check_wellness():
			wellness = self.check_wellness()
			self.food_info = UPC.objects.filter(upc_code=self.upc_code).values()[0]
			return self.food_info, {'success': 'Wellness Score already calculated.'}, wellness[0]['wellness']
		else:
			self.get_food_item()
			try:
				self.wellness = self.wellness_logic()
				# self.convert_dict_to_attributes() 
				#I am not sure it's the best idea to convert the dict to attributes because it makes applying the logic more verbose, but I am also not good at classes
				return self.food_info, self.api_response, self.wellness
			except (KeyError,TypeError) as e:
				return self.food_info, self.api_response, None

if __name__ == '__main__':
	
	#ISSUE: ad hoc testing be here; let's make formal tests ^__^__^
	# api_key = ''
	# api_id = ''

	# upc_code = '725342381715'
	# # upc_code = '99999;;;'

	
	# # UPC.objects.filter(upc_code=upc_code).values()
	# upc_code = '12000017421'
	# food_cat = 27

	# upc_key = UPC.objects.values_list('pk',flat=True).get(upc_code=upc_code)
	# cat_key = FoodCat.objects.values_list('pk', flat=True).get(load_cat=food_cat) #this will be right when db is reloaded
	# # NutRule.objects.values_list('pk', flat=True).get(food_cat_id_id=cat_key)
	# nut_key = NutRule.objects.values_list('pk', flat=True).get(food_cat_id_id=food_cat)
	
	# obj = WellScore(upc_id_id=upc_key, nut_id_id=nut_key,wellness=0)

	# u = Food(upc_code, food_cat, api_key, api_id)
	# context = u.get_food_item()

	# # context.update({'upc_code': upc_code, 'request': 'ok'})

	# pprint.pprint(context)
	pass