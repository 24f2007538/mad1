from flask import render_template, request, redirect, session, flash
from app import app
from backend.models import db, User, Student, Company, PlacementDrive, Application

def role_required(role):
    current_role = session.get("role")
    if current_role == role:
        return True
    return False

@app.route("/")
def home():
    return render_template("home.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, password=password).first()

        if user is None or not user.is_active:
            flash("invalid login")
            return redirect("/login")

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "company":
            company = Company.query.filter_by(user_id=user.id).first()

            if company and company.approval_status != "approved":
                flash("company not approved")
                return redirect("/login")

        return redirect(f"/{user.role}/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")






@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        email = request.form.get("email")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists")
            return redirect("/student/register")

        user = User(
            email=email,
            password=request.form.get("password"),
            role="student"
        )

        student = Student(
            user_id=None,  # temporary
            name=request.form.get("name"),
            roll_no=request.form.get("roll_no"),
            department=request.form.get("department"),
            cgpa=request.form.get("cgpa")
        )

        db.session.add(user)
        db.session.flush()  

        student.user_id = user.id
        db.session.add(student)

        db.session.commit()

        return redirect("/login")

    return render_template("sregister.html")


@app.route("/company/register", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        email = request.form.get("email")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists")
            return redirect("/company/register")

        user = User(
            email=email,
            password=request.form.get("password"),
            role="company"
        )

        company = Company(
            user_id=None,  
            company_name=request.form.get("company_name"),
            hr_contact=request.form.get("hr_contact"),
            website=request.form.get("website")
        )

        db.session.add(user)
        db.session.flush() 

        company.user_id = user.id
        db.session.add(company)

        db.session.commit()

        flash("waiting for admin approval")
        return redirect("/login")

    return render_template("cregister.html")







@app.route("/admin/dashboard")
def admin_dashboard():
    if not role_required("admin"):
        return redirect("/login")

    student_count = Student.query.count()
    company_count = Company.query.count()
    drive_count = PlacementDrive.query.count()
    application_count = Application.query.count()

    company_list = Company.query.all()
    drive_list = PlacementDrive.query.all()
    students_list = Student.query.all()

    return render_template(
        "adashboard.html",
        students=student_count,
        companies=company_count,
        drives=drive_count,
        applications=application_count,
        company_list=company_list,
        drive_list=drive_list,
        students_list=students_list
    )


@app.route("/admin/approve_company/<int:id>")
def approve_company(id):
    if not role_required("admin"):
        return redirect("/login")

    company = Company.query.get(id)
    if company:
        company.approval_status = "approved"
        db.session.commit()

    return redirect("/admin/dashboard")


@app.route("/admin/approve_drive/<int:id>")
def approve_drive(id):
    if not role_required("admin"):
        return redirect("/login")

    drive = PlacementDrive.query.get(id)
    if drive:
        drive.status = "approved"
        db.session.commit()

    return redirect("/admin/dashboard")






@app.route("/company/dashboard")
def company_dashboard():
    if not role_required("company"):
        return redirect("/login")

    user_id = session.get("user_id")
    company = Company.query.filter_by(user_id=user_id).first()

    drives = []
    if company:
        drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    return render_template("cdashboard.html", company=company, drives=drives)


@app.route("/company/create_drive", methods=["GET", "POST"])
def create_drive():
    if not role_required("company"):
        return redirect("/login")

    user_id = session.get("user_id")
    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        drive = PlacementDrive(
            company_id=company.id,
            job_title=request.form.get("job_title"),
            job_description=request.form.get("job_description"),
            eligibility_criteria=request.form.get("eligibility")
        )

        db.session.add(drive)
        db.session.commit()

        return redirect("/company/dashboard")

    return render_template("cdrive.html")

@app.route("/company/applications/<int:drive_id>")
def admin_view_applications(drive_id):
    if not role_required("company"):
        return redirect("/login")

    apps = Application.query.filter_by(drive_id=drive_id).all()
    apps_with_students = [(app, Student.query.get(app.student_id)) for app in apps]

    return render_template(
        "capplications.html",
        applications=apps_with_students,
        drive_id=drive_id
    )

@app.route("/admin/applications/<int:drive_id>")
def view_applications(drive_id):
    if not role_required("admin"):
        return redirect("/login")   

    apps = Application.query.filter_by(drive_id=drive_id).all()
    apps_with_students = [(app, Student.query.get(app.student_id)) for app in apps]

    return render_template(
        "aapplications.html",
        applications=apps_with_students,
        drive_id=drive_id
    )

#sjhdbfjsd last thing (check capplications and modify)
@app.route("/admin/viewstudent")
def view_students():
    if not role_required("admin"):
        return redirect("/login")   

    students = Student.query.all()

    return render_template(
        "adminviewstudent.html",
        students=students
    )


@app.route("/company/update_application_status/<int:id>", methods=["POST"])
def update_application_status(id):
    if not role_required("company"):
        return redirect("/login")

    status = request.form.get("status")
    allowed_status = ["waiting","shortlisted", "selected", "rejected"]

    if status in allowed_status:
        application = Application.query.get(id)
        if application:
            application.status = status
            db.session.commit()

    return redirect(request.referrer)





@app.route("/student/dashboard")
def student_dashboard():
    if not role_required("student"):
        return redirect("/login")

    drives = PlacementDrive.query.filter_by(status="approved").all()

    return render_template("sdashboard.html", drives=drives)


@app.route("/student/apply/<int:drive_id>")
def apply_drive(drive_id):
    if not role_required("student"):
        return redirect("/login")

    user_id = session.get("user_id")
    student = Student.query.filter_by(user_id=user_id).first()

    existing_application = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    if existing_application:
        flash("Already applied")
        return redirect("/student/dashboard")

    new_application = Application(
        student_id=student.id,
        drive_id=drive_id
    )

    db.session.add(new_application)
    db.session.commit()

    return redirect("/student/dashboard")