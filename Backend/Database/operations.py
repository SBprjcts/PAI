# db_operations.py
import psycopg2
from Models.user import Servicer, Customer
from Models.review import Review
from Models.service import Service
import datetime
from Tools.db_syntax import sqlToObject
import os
from typing import Optional
from psycopg2 import Binary


def getDbConnection():
    # Public IP
    hostname = '192.168.2.255'
    # Private IP
    # hostname = '76.71.0.245'

    database = 'PAIdb'
    username = 'paiadmin'
    password = 'Pai@124'
    port_id = 5432
    conn = psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=password,
        port=port_id
    )
    return conn


def get_sql_file_path(filename):
    # Get the directory of the current file (operations.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Move up one directory to the project root, then into the 'Database/sql' directory
    sql_dir = os.path.join(current_dir, '..', 'Database', 'sql')
    # Join the SQL directory with the filename
    file_path = os.path.join(sql_dir, filename)
    return file_path


def getImage(image_id: int):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('get_image.sql')
    with open(sql_file_path, 'r') as file:
        get_query = file.read()
    cur.execute(get_query, (image_id, ))

    image_binary = cur.fetchone()[1]

    cur.close()
    conn.close()

    return image_binary


def insertImage(email, binary_image) -> bool:
    conn = getDbConnection()
    cur = conn.cursor()
    
    # Get the id for the image
    sql_file_path = get_sql_file_path('get_num_images.sql')
    with open(sql_file_path, 'r') as file:
        get_query = file.read()
    cur.execute(get_query)
    image_id = int(cur.fetchone()[0]) + 1

    # Add the id of the image to servicer's "logo_id" column
    sql_file_path = get_sql_file_path('update_servicer_logo_id.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (image_id, email))

    # Insert image into image table
    sql_file_path = get_sql_file_path('insert_image.sql')
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    # cur.execute(insert_query, (psycopg2.Binary(binary_image),))
    cur.execute(insert_query, (image_id, binary_image))

    conn.commit()
    cur.close()
    conn.close()
    return image_id


def updateImage(image_id, binary_image) -> bool:
    conn = getDbConnection()
    cur = conn.cursor()
    
    # Get the id for the image

    # Insert image into image table
    sql_file_path = get_sql_file_path('update_image.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (binary_image, image_id))


    conn.commit()
    cur.close()
    conn.close()
    return True


def insertServicer(servicer: Servicer) -> bool:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file
    sql_file_path = get_sql_file_path('insert_servicer.sql')
    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    # Execute the query with parameters from the `user` object
    cur.execute(insert_query, (
        servicer.email, servicer.phone_number, servicer.company, servicer.password,
        servicer.address, servicer.description,
        servicer.reviews_ids, servicer.rating,
        servicer.services_ids, servicer.categories, str(servicer.date_created), 
        servicer.notifications_ids, servicer.radius, servicer.email_public, 
        servicer.phone_number_public, servicer.address_public, servicer.logo_id))
    conn.commit()
    cur.close()
    conn.close()


def getAllServicers() -> tuple[Servicer]:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all servicers
    sql_file_path = get_sql_file_path('get_all_servicers.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query)

    # Fetch all rows
    servicers_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # Chnage all tuples to Servicer objects
    servicers = []
    for x in servicers_sql:
        servicers.append(sqlToObject("Servicer", x))

    return servicers


def getServicerByCompany(company: str) -> Servicer:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all Servicers
    sql_file_path = get_sql_file_path('get_servicer_by_company.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (company,))

    # Fetch all rows
    servicers_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # No Servicer with that email
    if len(servicers_sql) < 1:
        return None

    # Return Servicer
    Servicer = sqlToObject("Servicer", servicers_sql[0])
    return Servicer


def getServicerInfo(email: str) -> Servicer:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all Servicers
    sql_file_path = get_sql_file_path('get_servicer_info.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (email,))

    # Fetch all rows
    servicers_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # No Servicer with that email
    if len(servicers_sql) < 1:
        return None

    # Return Servicer
    Servicer = sqlToObject("Servicer", servicers_sql[0])
    return Servicer


def getServiceInfo(id: int) -> Servicer:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all Servicers
    sql_file_path = get_sql_file_path('get_service_info.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (int(id),))

    # Fetch all rows
    services_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # No Servicer with that email
    if len(services_sql) < 1:
        return None

    # Return Servicer
    service = sqlToObject("Service", services_sql[0])
    return service


def insertCustomer(customer: Customer) -> bool:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file
    sql_file_path = get_sql_file_path('insert_customer.sql')
    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    # Execute the query with parameters from the `user` object
    cur.execute(insert_query, (
        customer.email, customer.phone_number, customer.full_name, customer.password,
        customer.address, customer.saved_posts_ids, str(customer.date_created), customer.reviews_ids))
    conn.commit()
    cur.close()
    conn.close()


def getAllCustomers() -> tuple[Customer]:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all customers
    sql_file_path = get_sql_file_path('get_all_customers.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query)

    # Fetch all rows
    customers_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # Chnage all tuples to Customer objects
    customers = []
    for x in customers_sql:
        customers.append(sqlToObject("Customer", x))

    return customers


def getCustomerInfo(email: str) -> Optional[Customer]:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all customers
    sql_file_path = get_sql_file_path('get_customer_info.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (email,))

    # Fetch all rows
    customers_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # No customer with that email
    if len(customers_sql) < 1:
        return None

    # Return Customer
    customer = sqlToObject("Customer", customers_sql[0])
    return customer


def updateReview(review: Review, old_rating) -> None:
    conn = getDbConnection()
    cur = conn.cursor()

    # Insert review into review table
    sql_file_path = get_sql_file_path('update_review.sql')
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    cur.execute(insert_query, (
        review.rating, review.description, review.id
    ))

    # Update servicer's rating
    sql_file_path = get_sql_file_path('update_servicer_rating.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (review.servicer_email, ))
    
    # Close the cursor and connection
    conn.commit()
    cur.close()
    conn.close()

    return True


def insertReview(review: Review) -> None:
    conn = getDbConnection()
    cur = conn.cursor()

    review.id = getReviewId()

    # Insert review into review table
    sql_file_path = get_sql_file_path('insert_review.sql')
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    cur.execute(insert_query, (
        review.id, review.rating, review.customer_email, review.servicer_email,
        review.description, str(review.date_created)
    ))

    # Add review id into customer
    sql_file_path = get_sql_file_path('add_review_customer.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (review.id, review.customer_email))

    # Add review id to servicer's reviews_ids
    sql_file_path = get_sql_file_path('add_review_servicer.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (review.id, review.servicer_email))

    # Update servicer's rating
    sql_file_path = get_sql_file_path('update_servicer_rating.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (review.servicer_email, ))
    
    # Close the cursor and connection
    conn.commit()
    cur.close()
    conn.close()

    return True


def updateServicerPassword(email: str, new_password: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_password.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_password, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerEmail(email: str, new_email: str):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('update_servicer_email.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_email, email))

    sql_file_path = get_sql_file_path('update_review_servicer_email.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_email, email))

    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerPhoneNumber(email: str, new_phone_number: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_phone_number.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_phone_number, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerAddress(email: str, new_address: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_address.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_address, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerCompany(email: str, new_company: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_company.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_company, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerDescription(email: str, new_description: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_description.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_description, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerRadius(email: str, new_radius: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_radius.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_radius, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerEmailPublic(email: str, new_public_email: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_email_public.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_public_email, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerPhoneNumberPublic(email: str, new_public_phone_number: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_phone_number_public.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_public_phone_number, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerAddressPublic(email: str, new_public_address: bool):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_address_public.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_public_address, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerInstagramProfile(email: str, new_instagram_profile: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_instagram_profile.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_instagram_profile, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerTiktokProfile(email: str, new_tiktok_profile: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_tiktok_profile.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_tiktok_profile, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateServicerFacebookProfile(email: str, new_facebook_profile: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_servicer_facebook_profile.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_facebook_profile, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def getReviewId() -> int:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all customers
    sql_file_path = get_sql_file_path('get_num_reviews.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query)

    # Fetch all rows
    reviews_sql = cur.fetchall()

    # Close the cursor and connection
    cur.close()
    conn.close()
    return int(reviews_sql[0][0]) + 1


def getReviewInfo(review_id) -> Review:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all Reviews
    sql_file_path = get_sql_file_path('get_review_info.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (review_id,))

    # Fetch all rows
    reviews_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # No Servicer with that email
    if len(reviews_sql) < 1:
        return None

    # Return Servicer
    review = sqlToObject("Review", reviews_sql[0])
    return review



def getServiceId() -> int:
    """
    Get service id for newly created service based on the maximum id that already exists.
    """
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('get_max_service_id.sql')
    with open(sql_file_path, 'r') as file:
        select_query = file.read()
    cur.execute(select_query)
    max_id = cur.fetchall()
    cur.close()
    conn.close()
    return int(max_id[0][0]) + 1


def insertService(service: Service) -> bool:
    """
    Insert a service into the "service" table.
    """
    # Get the id for the new service.
    service.id = getServiceId()

    conn = getDbConnection()
    cur = conn.cursor()

    # Define the path to your SQL file
    sql_file_path = get_sql_file_path('insert_service.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()

    # Execute the query with parameters from the `user` object
    cur.execute(insert_query, (
        service.id, service.owner_id, service.title, service.description, 
        service.price_min, service.price_max, service.discount, 
        str(service.date_created)))
    conn.commit()

    # Add the id to the servicers' "services_ids" list.
    sql_file_path = get_sql_file_path('update_servicer_services_ids.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (str(service.id), service.owner_id))
    conn.commit()

    cur.close()
    conn.close()
    return True


def updateService(service: Service):
    # Get the id for the new service.

    conn = getDbConnection()
    cur = conn.cursor()

    # Define the path to your SQL file
    sql_file_path = get_sql_file_path('update_service.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        update_query = file.read()

    # Execute the query with parameters from the `user` object
    cur.execute(update_query, (
        service.title, service.description, service.price_min, 
        service.price_max, service.discount, service.id))
    conn.commit()

    cur.close()
    conn.close()
    return True


def getAllServices() -> tuple[Servicer]:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all servicers
    sql_file_path = get_sql_file_path('get_all_services.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query)

    # Fetch all rows
    services_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # Chnage all tuples to Servicer objects
    services = []
    for x in services_sql:
        services.append(sqlToObject("Service", x))

    return services


def getServicerServices(owner: str) -> tuple[Servicer]:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all servicers
    sql_file_path = get_sql_file_path('get_servicer_services.sql')

    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        select_query = file.read()

    # Execute the query
    cur.execute(select_query, (owner, ))

    # Fetch all rows
    services_sql = cur.fetchall()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    # Chnage all tuples to Servicer objects
    services = []
    for x in services_sql:
        services.append(sqlToObject("Service", x))

    return services


def removeServicerService(owner, id):
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file for fetching all servicers
    sql_file_path = get_sql_file_path('remove_servicer_services.sql')
    with open(sql_file_path, 'r') as file:
        delete_query = file.read()
    cur.execute(delete_query, (int(id), ))
    conn.commit()

    # Remove the service from the servicer' "services_ids" list
    sql_file_path = get_sql_file_path('remove_service_servicer_services_ids.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (str(id), owner))
    conn.commit()

    # Don't forget to close the cursor and connection
    cur.close()
    conn.close()

    return True


def insertCategoryServicer(email, category):
    conn = getDbConnection()
    cur = conn.cursor()

    # Add the id to the servicers' "services_ids" list.
    sql_file_path = get_sql_file_path('insert_servicer_category.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (category, email))
    conn.commit()

    cur.close()
    conn.close()
    return True


def removeServicerCategory(email, category):
    conn = getDbConnection()
    cur = conn.cursor()

    # Add the id to the servicers' "services_ids" list.
    sql_file_path = get_sql_file_path('remove_servicer_category.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (category, email))
    conn.commit()

    cur.close()
    conn.close()
    return True


def insertCustomerSavedPostsIds(email: str, new_service_id: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('insert_customer_saved_posts_ids.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_service_id, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateCustomerPassword(email: str, new_password: str):
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('update_customer_password.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_password, email))
    conn.commit()
    cur.close()
    conn.close()
    return True


def updateCustomerEmail(email, new_email):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('update_customer_email.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_email, email))

    conn.commit()
    cur.close()
    conn.close()
    return True


def updateCustomerPhoneNumber(email, new_phone_number):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('update_customer_phone_number.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_phone_number, email))

    conn.commit()
    cur.close()
    conn.close()
    return True


def updateCustomerFullName(email, new_full_name):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('update_customer_full_name.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_full_name, email))

    conn.commit()
    cur.close()
    conn.close()
    return True


def updateCustomerAddress(email, new_address):
    conn = getDbConnection()
    cur = conn.cursor()

    sql_file_path = get_sql_file_path('update_customer_address.sql')
    with open(sql_file_path, 'r') as file:
        update_query = file.read()
    cur.execute(update_query, (new_address, email))

    conn.commit()
    cur.close()
    conn.close()
    return True
