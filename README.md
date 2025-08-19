
# [Blog Website](http://amalai320.pythonanywhere.com/)

A simple **Flask** application that implements user authentication and grants special rights to certain users using SQLite3 database.

This is one of the important milestones I have rached, since this project helped me a lot when I was working on Latte (see my GitHub repos), giving solid foundation in understanding REST APIs, User Authentication, Flask Apps, Backend-Frontend Communication, Database Integration, and Web Development in general.

Types of Users
- **Admin user** (the first one to register, or the user with id 1 in the database)
- **Registered user** (the user who is registered but not the admin)
- **Unregistered user** (the user who is not registered)

### Admin User
This user has the rights to create, modify, and delete the posts on the blog website. 
### Registered User
This user has the rights to comment the posts which were posted by admin user.
### Unregistered User
This user can only read the posts posted by admin user.
