from peewee import *
from playhouse.db_url import connect
from datetime import datetime

# mysql credentials
# user = root
# password = 123456

# # test db
# db = connect('sqlite+pool:///moving.db')

# production db
db = connect('mysql://root:123456@localhost:3306/topmovin_mymovingreviews')

db_moving = connect('mysql://root:123456@localhost:3306/companie_moving_companies_reviews')

class Company(Model):
    url = CharField(unique=True)
    title = CharField()
    rating = IntegerField()
    email = CharField(null=True)
    logo = CharField(null=True)
    website = CharField(null=True)
    phone = CharField(null=True)
    address = CharField(null=True)
    date_saved = DateTimeField(default=datetime.utcnow)
    logo_downloaded = BooleanField(default=False)

    class Meta:
        database = db
        table_name = 'companies'

    @classmethod
    def from_json(cls, json_data):
        states = json_data.pop('states')
        company, created = cls.get_or_create(url=json_data['url'], defaults=json_data)
        if created:
            with db.atomic():
                for state_name in states:
                    state, created = State.get_or_create(name=state_name)
                    CompanyState(company=company, state=state).save()
        return company

class Review(Model):
    author = CharField()
    date = CharField()
    rating = IntegerField()
    company = ForeignKeyField(Company)
    text = TextField(null=True)
    processed_text = TextField(null=True)
    date_saved = DateTimeField(default=datetime.utcnow)

    class Meta:
        database = db
        table_name = 'reviews'
        indexes = (
            (('author', 'company', 'date'), True),
        )

    @classmethod
    def from_json(cls, json_data):
        review, created = cls.get_or_create(author=json_data['author'], date=json_data['date'], company=json_data['company'], defaults=json_data)
        return review

    @classmethod
    def checkReview(cls, json_data):
        try:
            review = cls.get(author=json_data['author'], date=json_data['date'], company=json_data['company'])
            return review
        except:
            return False


class State(Model):
    name = CharField()

    class Meta:
        database = db
        table_name = 'states'


class CompanyState(Model):
    company = ForeignKeyField(Company)
    state = ForeignKeyField(State)

    class Meta:
        database = db
        table_name = 'company_state'


class Image(Model):
    url = CharField(unique=True)
    downloaded = BooleanField(default=False)
    filename = CharField(null=True)
    review = ForeignKeyField(Review)

    class Meta:
        database = db
        table_name = 'images'

    @classmethod
    def save_data(cls, url, review):
        image, created = cls.get_or_create(url=url, review=review)
        return image

class CompanyM(Model):
    c_id = PrimaryKeyField()
    comp_name = CharField()
    comp_stripname = CharField()
    image = CharField()
    email = CharField()
    website = CharField()
    phone = CharField()
    address = CharField()

    class Meta:
        database = db_moving
        table_name = 'moving_company'

    @classmethod
    def save_data(cls,json_data):
        data = {}
        data["comp_name"] = json_data["title"]
        data["comp_stripname"] = json_data["title"].strip().replace(" ","-").lower()
        data["image"] = json_data["logo"]
        data["address"] = json_data["address"]
        data["phone"] = json_data["phone"]
        data["email"] = json_data["email"]
        data["website"] = json_data["website"]
        company,created = cls.get_or_create(comp_name=data["comp_name"],comp_stripname=data["comp_stripname"],website=data["website"],defaults=data)
        return company
        

class ReviewM(Model):
    com_name = CharField()
    com_stripname = CharField()
    name = CharField()
    email = CharField()
    rating = IntegerField()
    review =  TextField(null=True)
    date = DateTimeField(default=datetime.utcnow)
    co_id = IntegerField()
    
    class Meta:
        database = db_moving
        table_name = 'review1'

    @classmethod
    def save_data(cls,review_json_data,comp_name, comp_stripname):
        data = {}
        data["com_name"] = comp_name
        data["com_stripname"] = comp_stripname   
        data["name"] = review_json_data["author"]
        data["rating"] = review_json_data["rating"]
        data["co_id"] = review_json_data["co_id"]
        data["review"] = review_json_data["text"]
        data["updated"] = "yes"
        
        review,created = cls.get_or_create(com_name=data["com_name"],com_stripname=data["com_stripname"],name=data["name"],rating = data["rating"], defaults=data)


db.create_tables([Company, Review, State, CompanyState, Image])
