import cloudinary
import cloudinary.uploader

import firebase_admin
from firebase_admin import db, credentials


cred = credentials.Certificate("setup/firebase.json")
firebase_admin.initialize_app(cred, {"databaseURL":"https://testing-65588-default-rtdb.firebaseio.com/"})
#creating ref for root
root_ref = db.reference("/")
images_ref = db.reference("/images")


cloudinary.config(
    cloud_name="dtwinn6ii",
    api_key="918731684835228",
    api_secret="Gkotgix9G0MJFezAxirmlbyniPg"
)

result = cloudinary.uploader.upload("images_detect/test.jpeg")

print(result["secure_url"])

db.reference("/images/input").set(result["secure_url"])
