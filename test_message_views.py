"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")



    def test_add_unauthorized_message(self):
        """can someone who is not logged in create a message"""
        with self.client as client:
            response = client.post('/messages/new', data={"text": "testing message"}, follow_redirects=True)
            html = response.get_data(as_text=True)
            
            self.assertEquals(response.status_code,200)
            self.assertIn("Access unauthorized.", html)


    def test_delete_message(self):
        "testing deleting an existing message"

        message = Message(
            id = 12,
            text = "testing message text",
            user_id= self.testuser.id)
        
        db.session.add(message)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

                response = client.post("/messages/12/delete",follow_redirects=True)
                self.assertEquals(response.status_code,200)

                messages = Message.query.all()
                m = Message.query.get(12)
                self.assertNotIn(m,messages)

    def test_unauthorized_delete_message(self):
            """can a user delete a message created by another user"""
            unauthorized_user = User.signup(username='unauthorized', email="testing@test.com", password="secret",
                                            image_url=None)
            unauthorized_user.id=1111111

            test_user_message= Message(id=12345,text='you cant delete me', user_id=self.testuser.id)
            db.session.add_all([unauthorized_user,test_user_message])
            db.session.commit()

            with self.client as client:
                with client.session_transaction() as session:
                    session[CURR_USER_KEY] = 1111111
                    
                    response = client.post('messages/12435/delete', follow_redirects=True)
                    html = response.get_data(as_text=True)
                    self.assertEquals(response.status_code,200)
                    self.assertIn("Access unauthorized", html)
