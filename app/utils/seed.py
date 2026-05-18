from app import db, bcrypt
from app.models.models import User, Role, School, Department, Specialization

def seed_admin():
    if not User.query.filter_by(username='admin').first():
        pw = bcrypt.generate_password_hash('Admin@FedPoly2024').decode('utf-8')
        admin = User(username='admin', email='admin@fedpolynas.edu.ng',
                     password_hash=pw, role=Role.ADMIN,
                     must_change_password=True)
        db.session.add(admin)
        db.session.commit()
        print('✅ Default admin created: username=admin, password=Admin@FedPoly2024')

def seed_departments():
    """Seed default FedPoly Nasarawa schools/departments/specializations."""
    if School.query.first():
        return  # already seeded

    data = [
        {
            'name': 'School of Information Technology',
            'short': 'SIT',
            'departments': [
                {
                    'name': 'Computer Science',
                    'specializations': [
                        {'name': 'Networking and Cloud Computing',    'levels': 'HND 1,HND 2'},
                        {'name': 'Software Engineering & Web Development', 'levels': 'HND 1,HND 2'},
                    ]
                },
                {'name': 'Computer Engineering',      'specializations': []},
                {'name': 'Information Technology',    'specializations': []},
                {'name': 'Cyber Security',            'specializations': []},
            ]
        },
        {
            'name': 'School of Business Studies',
            'short': 'SBS',
            'departments': [
                {'name': 'Accountancy',               'specializations': []},
                {'name': 'Business Administration',   'specializations': []},
                {'name': 'Marketing',                 'specializations': []},
                {'name': 'Banking and Finance',       'specializations': []},
            ]
        },
        {
            'name': 'School of Engineering',
            'short': 'SOE',
            'departments': [
                {'name': 'Electrical Engineering',    'specializations': []},
                {'name': 'Mechanical Engineering',    'specializations': []},
                {'name': 'Civil Engineering',         'specializations': []},
            ]
        },
        {
            'name': 'School of Environmental Studies',
            'short': 'SES',
            'departments': [
                {'name': 'Architecture',              'specializations': []},
                {'name': 'Estate Management',         'specializations': []},
                {'name': 'Quantity Surveying',        'specializations': []},
            ]
        },
    ]

    for s_data in data:
        school = School(name=s_data['name'], short_name=s_data['short'])
        db.session.add(school)
        db.session.flush()
        for d_data in s_data['departments']:
            dept = Department(school_id=school.id, name=d_data['name'])
            db.session.add(dept)
            db.session.flush()
            for sp_data in d_data['specializations']:
                spec = Specialization(department_id=dept.id,
                                      name=sp_data['name'],
                                      levels=sp_data['levels'])
                db.session.add(spec)

    db.session.commit()
    print('✅ Default schools, departments and specializations seeded')
