import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dtwinn6ii",
    api_key="918731684835228",
    api_secret="Gkotgix9G0MJFezAxirmlbyniPg"
)

result = cloudinary.uploader.upload("sample_images/test.jpg")

print(result["secure_url"])
