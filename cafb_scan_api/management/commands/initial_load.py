from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from cafb_scan_api.models import UPC, FoodCat, NutRule

class Command(BaseCommand):
	help = 'Loads initial UPC data, food categories, and wellness rules'

	def handle(self, *args, **options):

		PATH = settings.BASE_DIR

		# load products
		self.stdout.write('Loading products ...')
		products  = PATH +'/cafb_scan_api/fixtures/products.csv'

		self.stdout.write(products)
		with open(products, 'r+') as f:
			data = list(f)

		for product in data[1:]:
			product = unicode(product, 'utf-8').replace('\n', '').split(',')

			obj = UPC(
						upc_code=product[21],
						item_name=product[23],
						brand_id=product[0],
						brand_name=product[3],
						item_image=product[22],
						ingredients=product[24],
						calories=float(product[4]),
						calories_from_fat=float(product[5]),
						total_fat=float(product[52]),
						saturated_fat=float(product[42]),
						cholesterol=float(product[8]),
						sodium=float(product[47]),
						total_carb=float(product[50]),
						dietary_fiber=float(product[11]),
						sugars=float(product[48]),
						protein=float(product[39]),
						vitamin_a_dv=float(product[54]),
						vitamin_c_dv=float(product[55]),
						calcium_dv=float(product[6]),
						iron_dv=float(product[25]),
						serving_per_cont=float(product[43]),
						serving_size_qty=float(product[56]),
						serving_size_unit=product[57],
						data_source='CSV'
			)

			obj.save()

			self.stdout.write(self.style.SUCCESS('Product name: Added "%s"' % product[23]))


		# load food categories
		self.stdout.write('Loading food categories ...')
		cats  = PATH +'/cafb_scan_api/fixtures/categories.csv'

		self.stdout.write(cats)
		with open(cats, 'r+') as f:
			data = list(f)

		for cat in data[1:]:
			cat = unicode(cat, 'utf-8').replace('\n', '').split(',')

			obj = FoodCat(
					load_cat=cat[0],
					abbr=cat[1],
					name=cat[2],
					description=cat[3],
					notes=cat[4]
			)

			obj.save()

			self.stdout.write(self.style.SUCCESS('Catgory: Added "%s"' % cat[1]))


		# load nutrition rules
		self.stdout.write('Loading nutrition rules ...')
		nuts  = PATH +'/cafb_scan_api/fixtures/nutrules.csv'

		self.stdout.write(nuts)
		with open(nuts, 'r+') as f:
			data = list(f)

		for nut in data[1:]:
			nut = unicode(nut, 'utf-8').replace('\n', '').split(',')

			obj = NutRule(
					nutrient=nut[1],
					nutritional_field=nut[2],
					rule_type=nut[3],
					value=nut[4],
					wellness=int(nut[5])		
					)
			obj.food_cat_id_id=FoodCat.objects.values_list('pk', flat=True).get(load_cat=nut[0])
			obj.save()

			self.stdout.write(self.style.SUCCESS('Nutrition Rule: Added "%s"' % nut[1]))