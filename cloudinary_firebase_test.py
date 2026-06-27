import cloudinary
import cloudinary.uploader

import firebase_admin
from firebase_admin import db, credentials


cred = credentials.Certificate("firebase/firebase_new.json")
firebase_admin.initialize_app(cred, {"databaseURL":"https://testing-65588-default-rtdb.firebaseio.com/"})
#creating ref for root
root_ref = db.reference("/")
images_ref = db.reference("/images")
db.reference("/objects/object_detected1").set(True)