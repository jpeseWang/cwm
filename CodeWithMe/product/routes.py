from product import app, db
from flask import render_template, redirect, url_for, flash, abort, request
from product.models import Project, User, Comment
from product.forms import RegisterForm, LoginForm, CreateForm
from flask_login import login_user, logout_user, login_required, current_user

@app.route("/")
@app.route("/home")
def home_page():
	return render_template("home.html")

@app.route("/projects")
@login_required
def projects_page():
	projects = Project.query.all()
	return render_template("projects.html", projects= projects)

@app.route("/about_us")
def about_us_page():
	return render_template("about_us.html")

@app.route("/fpt")
def fpt_page():
	return render_template("fpt.html")

@app.route("/first")
def first_page():
	return render_template("first.html")


@app.route("/register", methods= ['GET', 'POST'])
def register_page():
	form = RegisterForm()
	if form.validate_on_submit():
		user_to_create = User(username= form.username.data,
							email_address= form.email_address.data,
							 password= form.password_1.data)
		with app.app_context():
			db.session.add(user_to_create)
			db.session.commit()
			login_user(user_to_create)
		
		flash(f"Account created successfully! You are now logged in as {user_to_create.username}.", category= "success")

		return redirect(url_for("projects_page"))

	if form.errors != {}: 
		for err_msg in form.errors.values():
			flash(f"There was an error with creating a user: {err_msg}", category= "danger")

	return render_template("register.html", form= form)

@app.route("/login", methods= ['GET', 'POST'])
def login_page():
	form = LoginForm()
	if form.validate_on_submit():
		with app.app_context():
			attempted_user = User.query.filter_by(username= form.username.data).first()
			if attempted_user and attempted_user.check_password_correction(attempted_password= form.password.data):
				login_user(attempted_user)
				flash(f"Success! You are logged in as {attempted_user.username}.", category= "success")
				return redirect(url_for("projects_page"))
			else:
				flash("Username and password are incorrect! Please try again!", category= "danger")

	return render_template("login.html", form= form)

@app.route("/logout")
def logout_page():
	logout_user()
	flash("You have been logged out!", category= "info")
	return redirect(url_for("home_page"))

@app.route("/projects/create", methods= ['GET', 'POST'])
@login_required
def create_page():
	form = CreateForm()
	if form.validate_on_submit():
		proj_to_create = Project(name= form.name.data, contributor= current_user.username, description= form.description.data,
									source_code= form.source_code.data)
		with app.app_context():
			db.session.add(proj_to_create)
			db.session.commit()
			flash(f"Project {proj_to_create.name} created successfully!", category= "success")

		return redirect(url_for("projects_page"))

	if form.errors != {}:
		for err_msg in form.errors.values():
			flash(f"There was an error with creating a project: {err_msg}", category= "danger")

	return render_template("create.html", form= form)



@app.route("/projects/<int:project_id>", methods= ['GET', 'POST'])
@login_required
def project(project_id):
	project= Project.query.filter_by(id= project_id).first()
	comments= Comment.query.filter_by(project_id= project_id)
	return render_template("project.html", project= project, comments= comments)

@app.route("/process/<int:project_id>", methods= ['GET', "POST"])
@login_required
def process(project_id):
	project= Project.query.filter_by(id= project_id).first()
	if request.method == 'POST':
		raw_data = request.form['raw_data']
	return render_template("project.html", project= project, raw_data= raw_data)



@app.route("/projects/<int:project_id>/edit", methods= ['GET', 'POST'])
@login_required
def edit_page(project_id):
	project = Project.query.filter_by(id= project_id).first()
	if project.contributor != current_user.username:
		abort(403)

	form = CreateForm()
	if form.validate_on_submit():
		with app.app_context():
			db.session.delete(project)
			db.session.add(Project(name= form.name.data, contributor= current_user.username, description= form.description.data,
									source_code= form.source_code.data))

			db.session.commit()
			flash(f"Project {project.name} has been edited!", category= "success")
		
		return redirect(url_for("project", project_id= project.id))
	elif request.method == 'GET':
		form.name.data = project.name
		form.description.data = project.description
		form.source_code.data = project.source_code

	if form.errors != {}:
		for err_msg in form.errors.values():
			flash(f"There was an error with editing a project: {err_msg}", category= "danger")

	return render_template("edit.html", project= project, form= form)

@app.route("/projects/<int:project_id>/delete")
@login_required
def delete_page(project_id):
	project = Project.query.filter_by(id= project_id).first()
	if not project:
		flash("Project does not exist.", category= 'error')
	elif current_user.username != project.contributor:
		flash("You do not have permission to delete this project.")
	else:
		with app.app_context():
			db.session.delete(project)
			db.session.commit()
			flash(f"Project {project.name} deleted successfully.", category= "success")

	return redirect(url_for("projects_page"))

@app.route("/create-comment/<int:project_id>", methods=['POST'])
@login_required
def create_comment(project_id):
	text = request.form.get('text')
	if not text:
		flash("Comment can not be empty", category= "error")
	else:
		project = Project.query.filter_by(id= project_id).first()
		if project:
			comment = Comment(author= current_user.username, project_id= project_id, text= text)
			with app.app_context():
				db.session.add(comment)
				db.session.commit()
		else:
			flash("Project does not exist", category= "error")

	return redirect(url_for("project", project_id= project_id))