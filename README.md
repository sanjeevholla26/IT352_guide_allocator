# IT303_Btech_Guide_Allocator

## Set-up Instructions :

- Clone the repository and enter into the folder using the below command.
```bash
git clone https://github.com/sanjeevholla26/IT352_guide_allocator.git
cd IT352_guide_allocator
```
- Create a virtual environment by:
```bash
python -m venv venv
source ./venv/bin/activate
```
- Install all the required dependencies by:
```bash
pip install -r requirements.txt
```
- Fill in the credentials within the `settings.py` file.
- Run the below command to establish a proper database.
```bash
bash db_reset.sh
```
- Run the below command to create the superuser admin.
```bash
python manage.py createsuperuser
```
- Assign the admin you created by running the `role_builder.py` file.
- Redis Setup :
  - Install Redis
  - Remove comment from bind 127.0.0.1 in .conf file(redis.windows.config)
  - Start redis server using config file in Redis installed directory [redis-server ./redis.windows.config]
  - To start redis for out task(email): python -m celery -A Project_Guide_Allocator worker --pool=solo -l info
  - Create a logs folder and create a file named django.logs

## Permissions 

1. Roles - admin
   
   actions - login,home,register,add_student,add_event,edit_event,add_faculty,admin_all_events,create_cluster,run_allocation,reset_allocation,admin_show_clash,admin_resolve_clash,add_permissions,generate_student_pdf,generate_faculty_pdf,generate_admin_pdf,event_results,logout_view

3. Roles - Student
   
   actions - all_events,event,create_or_edit_choicelist,choice_lock_otp,logout_view

5. Roles - Faculty
   
   actions - show_all_clashes,resolve_clash,eligible_events,logout_view,event_results

app name - Allocator (common for all)

