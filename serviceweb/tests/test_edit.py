from webtest.app import AppError
from serviceweb.tests.support import BaseTest


class EditTest(BaseTest):
    def test_edit_project(self):
        # first attempt fails since we're not logged in
        self.assertRaises(AppError, self.app.get, '/projects/1/edit')

        # now logging in
        with self.logged_in():
            project = self.app.get('/projects/1/edit')
            form = project.forms[0]
            old_name = form['name'].value
            form['name'] = 'new name'
            form.submit()

            # let's check it changed
            self.assertTrue(b'new name' in self.app.get('/projects/1').body)

            # change it back to the old value
            project = self.app.get('/projects/1/edit')
            form = project.forms[0]
            form['name'] = old_name
            form.submit()

    def test_edit_user(self):
        with self.logged_in():
            user = self.app.get('/users/1/edit')
            form = user.forms[0]
            old_name = form['firstname'].value
            form['firstname'] = 'new name'
            form.submit()

            # let's check it changed
            self.assertTrue(b'New name' in self.app.get('/users/1').body)

            # change it back to the old value
            user = self.app.get('/users/1/edit')
            form = user.forms[0]
            form['firstname'] = old_name
            form.submit()

            # let's control we don't have a dupe
            users = self.app.get('/users')
            tds = users.html.find_all('td')
            self.assertEqual(len([td.text for td in tds
                                  if td.text == old_name]), 1)