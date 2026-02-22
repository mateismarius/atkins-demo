from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time, date
import random

class Command(BaseCommand):
    help = 'Seed demo data for NightOps Platform'

    def handle(self, *args, **options):
        self.stdout.write('Seeding NightOps demo data...')
        today = timezone.now().date()

        # Users
        admin = User.objects.create_superuser('admin', 'admin@nightops.local', 'admin',
            first_name='Marius', last_name='Admin')
        
        users_data = [
            ('jsmith', 'John', 'Smith'), ('awright', 'Angela', 'Wright'),
            ('mbrown', 'Mike', 'Brown'), ('sjones', 'Sarah', 'Jones'),
            ('dclark', 'Dave', 'Clark'), ('lwilson', 'Lisa', 'Wilson'),
            ('rpatel', 'Raj', 'Patel'), ('kthomas', 'Karen', 'Thomas'),
            ('ptaylor', 'Paul', 'Taylor'), ('nwalker', 'Nina', 'Walker'),
            ('bharris', 'Ben', 'Harris'), ('cmartin', 'Claire', 'Martin'),
        ]
        users = []
        for uname, fn, ln in users_data:
            u = User.objects.create_user(uname, f'{uname}@nightops.local', 'pass123',
                first_name=fn, last_name=ln)
            users.append(u)

        # Teams
        from core.models import Team, TeamMember
        teams_data = [
            ('T01', 'Alpha Crew', 'night', 'Terminal 2 - Arrivals'),
            ('T02', 'Bravo Squad', 'night', 'Terminal 2 - Departures'),
            ('T03', 'Charlie Unit', 'night', 'Terminal 5 - North'),
            ('T04', 'Delta Force', 'night', 'Terminal 5 - South'),
            ('T05', 'Echo Team', 'night', 'Airfield - Taxiways'),
            ('T06', 'Foxtrot Group', 'night', 'Baggage Tunnels'),
            ('T07', 'Golf Crew', 'night', 'Terminal 3 - Main'),
            ('T08', 'Hotel Squad', 'night', 'Cargo Area'),
            ('T09', 'India Unit', 'night', 'Terminal 4 - East'),
            ('T10', 'Juliet Team', 'night', 'Utilities & MEP'),
            ('T11', 'Kilo Group', 'night', 'Perimeter & Roads'),
            ('T12', 'Lima Crew', 'night', 'Emergency Systems'),
        ]
        teams = []
        for i, (code, name, shift, area) in enumerate(teams_data):
            t = Team.objects.create(code=code, name=name, shift=shift, area=area,
                leader=users[i], is_active=True)
            teams.append(t)

        # Team Members
        roles = ['leader', 'supervisor', 'operative', 'operative', 'engineer', 'apprentice']
        for i, u in enumerate(users):
            TeamMember.objects.create(user=u, team=teams[i], role='leader',
                phone=f'+44 7700 {900100+i}', employee_id=f'EMP{1000+i}', is_on_shift=True)
        
        # Extra members
        extra_names = [
            ('Tom', 'Baker'), ('Emma', 'Davis'), ('James', 'Lee'), ('Sophie', 'White'),
            ('Ryan', 'Green'), ('Laura', 'King'), ('Mark', 'Hill'), ('Amy', 'Scott'),
            ('Chris', 'Hall'), ('Katie', 'Adams'), ('Dan', 'Young'), ('Rachel', 'Evans'),
            ('Sam', 'Roberts'), ('Helen', 'Allen'), ('George', 'Cook'), ('Emily', 'Ward'),
            ('Jack', 'Turner'), ('Olivia', 'Morgan'), ('Harry', 'Wood'), ('Chloe', 'Brooks'),
        ]
        for idx, (fn, ln) in enumerate(extra_names):
            eu = User.objects.create_user(f'{fn.lower()}{ln.lower()[:3]}', f'{fn.lower()}@nightops.local', 'pass123',
                first_name=fn, last_name=ln)
            team = teams[idx % len(teams)]
            role = random.choice(['operative', 'operative', 'supervisor', 'engineer', 'apprentice'])
            TeamMember.objects.create(user=eu, team=team, role=role,
                phone=f'+44 7700 {900200+idx}', employee_id=f'EMP{2000+idx}',
                is_on_shift=random.choice([True, True, True, False]))

        # Projects
        from projects.models import Project, Task, Milestone
        projects_data = [
            ('HEX-001', 'T5 Taxiway Resurfacing', 'active', 'critical', 'Resurfacing of taxiways Alpha and Bravo connecting Terminal 5', 2500000, 65),
            ('HEX-002', 'T2 Baggage System Upgrade', 'active', 'high', 'Complete replacement of baggage handling conveyors in Terminal 2', 4200000, 40),
            ('HEX-003', 'Perimeter Fence Renewal', 'active', 'medium', 'Phase 3 of airfield perimeter security fence replacement', 890000, 80),
            ('HEX-004', 'MEP Distribution Upgrade', 'planning', 'high', 'Electrical distribution upgrade for Terminal 3 and 4', 3100000, 10),
            ('HEX-005', 'Emergency Lighting Retrofit', 'active', 'medium', 'LED retrofit of emergency lighting across all terminals', 450000, 55),
            ('HEX-006', 'Cargo Tunnel Waterproofing', 'on_hold', 'high', 'Waterproofing and drainage works in cargo area tunnels', 1200000, 30),
            ('HEX-007', 'T4 Departure Lounge Refurb', 'completed', 'medium', 'Interior refurbishment including flooring and ceilings', 780000, 100),
            ('HEX-008', 'Airfield Drainage Phase 2', 'active', 'critical', 'Major drainage improvement works on southern apron', 5600000, 25),
        ]
        projects = []
        for code, name, status, priority, desc, budget, progress in projects_data:
            p = Project.objects.create(
                code=code, name=name, status=status, priority=priority,
                description=desc, budget=budget, progress=progress,
                manager=random.choice(users[:4]),
                start_date=today - timedelta(days=random.randint(30, 180)),
                end_date=today + timedelta(days=random.randint(30, 365)),
                location='Heathrow Airport'
            )
            projects.append(p)

        # Tasks
        task_titles = [
            'Site survey and assessment', 'Material procurement', 'Ground preparation works',
            'Install temporary barriers', 'Excavation and removal', 'Foundation laying',
            'Cable routing and installation', 'Structural steelwork', 'Concrete pouring',
            'Waterproofing application', 'Electrical first fix', 'Mechanical installation',
            'Commissioning tests', 'Quality inspection', 'Snagging and defects',
            'Client sign-off preparation', 'As-built documentation', 'Health & safety review',
            'Environmental compliance check', 'Night works coordination',
        ]
        statuses = ['backlog', 'todo', 'in_progress', 'review', 'done']
        priorities = ['low', 'medium', 'high', 'urgent']
        for p in projects:
            num_tasks = random.randint(8, 15)
            selected = random.sample(task_titles, min(num_tasks, len(task_titles)))
            for title in selected:
                Task.objects.create(
                    project=p, title=title,
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    assigned_to=random.choice(users),
                    due_date=today + timedelta(days=random.randint(-10, 60)),
                    progress=random.randint(0, 100),
                )

        # Milestones
        for p in projects:
            for ms_title in ['Design Approval', 'Phase 1 Complete', 'Commissioning', 'Handover']:
                Milestone.objects.create(
                    project=p, title=ms_title,
                    due_date=p.start_date + timedelta(days=random.randint(30, 180)),
                    completed=random.choice([True, False]),
                )

        # QA - Inspections
        from qa.models import Inspection, InspectionItem, NonConformance
        inspection_areas = ['Taxiway Alpha', 'Terminal 2 Gate 5', 'Cargo Tunnel Section B',
            'Perimeter Zone 7', 'T5 North Pier', 'Baggage Hall Level -1',
            'Apron Stand 421', 'MEP Room T3-E4']
        insp_types = ['Structural', 'Electrical', 'Health & Safety', 'Environmental', 'Fire Safety']

        for i in range(20):
            insp = Inspection.objects.create(
                project=random.choice(projects[:5]),
                inspector=random.choice(users[:4]),
                date=timezone.now() - timedelta(days=random.randint(0, 30)),
                area=random.choice(inspection_areas),
                inspection_type=random.choice(insp_types),
                status=random.choice(['completed', 'completed', 'completed', 'failed', 'scheduled']),
                score=random.randint(55, 100),
            )
            # Items
            items_desc = [
                'PPE compliance check', 'Fire extinguisher inspection', 'Scaffold tagging verification',
                'Electrical isolation confirmed', 'Housekeeping standard', 'Signage and barriers',
                'Material storage check', 'Welfare facilities', 'Emergency exit clearance',
                'Permit display verification',
            ]
            for desc in random.sample(items_desc, random.randint(5, 8)):
                compliant = random.random() > 0.15
                InspectionItem.objects.create(
                    inspection=insp, description=desc,
                    is_compliant=compliant,
                    severity=random.choice(['info', 'minor', 'major']) if not compliant else 'info',
                    notes='' if compliant else 'Requires immediate attention',
                )

        # NCRs
        ncr_titles = [
            'Concrete pour below specification strength', 'Incorrect cable sizing installed',
            'Missing fire stop in penetration', 'Damaged waterproof membrane',
            'Steel connections not torqued to spec', 'Drainage fall incorrect',
            'Incomplete welding on structural steel', 'Missing insulation on pipework',
            'Incorrect paint system applied', 'Scaffold missing base plates',
        ]
        for title in ncr_titles:
            NonConformance.objects.create(
                project=random.choice(projects[:5]),
                title=title,
                description=f'Non-conformance identified during routine inspection. {title.lower()} found to be non-compliant with project specifications.',
                severity=random.choice(['minor', 'minor', 'major', 'critical']),
                status=random.choice(['open', 'investigating', 'corrective_action', 'closed']),
                raised_by=random.choice(users[:4]),
                assigned_to=random.choice(users[:6]),
                due_date=today + timedelta(days=random.randint(1, 30)),
            )

        # Briefing - Pre-briefing forms for today
        from briefing.models import PreBriefingForm, NightBriefing, BriefingActionItem
        for team in teams[:9]:  # 9 of 12 submitted
            PreBriefingForm.objects.create(
                team=team, shift_date=today, submitted_by=team.leader,
                staff_present=random.randint(4, 7),
                staff_expected=random.randint(5, 8),
                absentees=random.choice(['', '', 'J. Davis - sick leave', 'M. Turner - annual leave']),
                equipment_status=random.choice(['all_ok', 'all_ok', 'all_ok', 'minor_issues']),
                ppe_check_completed=random.choice([True, True, True, False]),
                safety_concerns=random.choice([
                    '', '', '',
                    'Wet conditions on taxiway - slip hazard',
                    'Restricted visibility due to fog',
                    'Heavy plant movements near work zone',
                ]),
                near_misses=random.choice(['', '', 'Forklift near miss at cargo bay entrance']),
                pending_tasks_from_previous=random.choice([
                    'Complete cable pulling in duct 7B',
                    'Finish barrier installation at gate 5',
                    'Awaiting concrete test results',
                    '',
                ]),
                planned_tasks_tonight=random.choice([
                    'Continue taxiway resurfacing section 3',
                    'Install new conveyor belt sections 12-15',
                    'Fence panel installation zones 14-18',
                    'Cable tray installation level -2',
                    'Emergency lighting replacement T3 corridors',
                    'Tunnel drainage pump installation',
                ]),
                blockers=random.choice(['', '', 'Waiting for materials delivery', 'Access restricted until 23:00']),
                materials_needed=random.choice(['', '50m Cat6 cable', '20x fence panels']),
                permits_in_place=random.choice([True, True, True, False]),
                method_statements_reviewed=random.choice([True, True, False]),
                weather_impact=random.choice(['none', 'none', 'none', 'minor']),
                risk_rating=random.choice(['green', 'green', 'green', 'amber', 'red']),
            )

        # Past forms
        for days_ago in range(1, 8):
            past_date = today - timedelta(days=days_ago)
            for team in teams:
                PreBriefingForm.objects.create(
                    team=team, shift_date=past_date, submitted_by=team.leader,
                    staff_present=random.randint(4, 7), staff_expected=6,
                    equipment_status='all_ok', ppe_check_completed=True,
                    planned_tasks_tonight='Standard night operations',
                    risk_rating=random.choice(['green', 'green', 'amber']),
                )

        # Night Briefings (past)
        for days_ago in range(1, 8):
            past_date = today - timedelta(days=days_ago)
            nb = NightBriefing.objects.create(
                date=past_date, conducted_by=admin,
                start_time=time(21, 0), end_time=time(21, 30),
                total_staff_present=random.randint(55, 65),
                total_staff_expected=65,
                safety_briefing='Standard safety briefing. Reminded all teams about PPE requirements and pedestrian routes.',
                key_decisions=f'Prioritised taxiway works due to window availability.',
                overall_risk=random.choice(['green', 'green', 'amber']),
            )
            for j in range(random.randint(2, 5)):
                BriefingActionItem.objects.create(
                    briefing=nb,
                    description=random.choice([
                        'Chase materials delivery for T2 project',
                        'Update method statement for crane operation',
                        'Arrange additional lighting for airfield works',
                        'Confirm permit extension with HAL',
                        'Schedule toolbox talk on manual handling',
                    ]),
                    assigned_to=random.choice(users[:6]),
                    team=random.choice(teams),
                    priority=random.choice(['low', 'medium', 'high']),
                    status=random.choice(['pending', 'in_progress', 'done']),
                )

        # Monitoring - Team Status
        from monitoring.models import TeamStatus, ActivityLog, IncidentReport
        status_options = ['active', 'active', 'active', 'on_break', 'delayed']
        current_tasks = [
            'Taxiway resurfacing Section 3 Layer 2',
            'Conveyor belt installation Section 12',
            'Fence panel erection Zone 14',
            'Cable tray installation Duct 7B',
            'LED lighting retrofit Corridor C',
            'Pump installation Chamber 4',
            'Floor tiling Area 2B',
            'Drainage channel Section 8',
            'Steelwork installation Frame 6',
            'Fire alarm cabling Level -1',
            'Scaffold erection Stand 421',
            'Generator maintenance Unit 3',
        ]
        for i, team in enumerate(teams):
            TeamStatus.objects.create(
                team=team, date=today,
                current_task=current_tasks[i],
                location=team.area,
                progress=random.randint(10, 85),
                status=random.choice(status_options),
                staff_count=random.randint(4, 7),
            )

        # Activity Logs
        actions = ['task_started', 'task_completed', 'break_start', 'break_end', 'update', 'delay']
        now = timezone.now()
        for i in range(50):
            ActivityLog.objects.create(
                team=random.choice(teams),
                user=random.choice(users),
                action=random.choice(actions),
                details=random.choice([
                    'Started concrete pour on section 3',
                    'Completed cable pulling in duct 7B',
                    'Scheduled break 01:00-01:30',
                    'Updated progress to 65%',
                    'Delay due to material shortage',
                    'Toolbox talk completed',
                    'Equipment check passed',
                ]),
                timestamp=now - timedelta(minutes=random.randint(0, 480)),
            )

        # Incidents
        IncidentReport.objects.create(
            team=teams[4], reported_by=users[4],
            title='Near miss - vehicle proximity',
            description='Airfield vehicle passed within 2m of work zone without prior warning.',
            severity='near_miss', location='Taxiway Alpha',
            immediate_action='Work stopped. Briefed all operatives on vehicle awareness.',
            is_resolved=False,
        )

        # Planning
        from planning.models import ShiftPlan, ShiftAssignment, Resource
        
        # This week's plans
        for i in range(7):
            plan_date = today - timedelta(days=today.weekday()) + timedelta(days=i)
            plan = ShiftPlan.objects.create(
                date=plan_date, shift='night', created_by=admin,
                is_published=plan_date <= today,
            )
            for team in teams:
                ShiftAssignment.objects.create(
                    plan=plan, team=team, area=team.area,
                    task_description=random.choice(current_tasks),
                    priority=random.choice(['normal', 'normal', 'high', 'critical']),
                    estimated_hours=random.choice([6, 7, 8, 10]),
                    status='in_progress' if plan_date == today else ('completed' if plan_date < today else 'planned'),
                )

        # Resources
        resources_data = [
            ('Telehandler #1', 'vehicle'), ('Telehandler #2', 'vehicle'),
            ('Transit Van HX-01', 'vehicle'), ('Transit Van HX-02', 'vehicle'),
            ('Cherry Picker CP-01', 'vehicle'), ('Excavator EX-01', 'vehicle'),
            ('Generator 100kVA #1', 'equipment'), ('Generator 100kVA #2', 'equipment'),
            ('Tower Light TL-01', 'equipment'), ('Tower Light TL-02', 'equipment'),
            ('Tower Light TL-03', 'equipment'), ('Compressor CM-01', 'equipment'),
            ('Concrete Mixer MX-01', 'equipment'), ('Welder WD-01', 'tool'),
            ('Core Drill CD-01', 'tool'), ('Cable Puller CP-01', 'tool'),
            ('Barrier Set BS-01', 'material'), ('Barrier Set BS-02', 'material'),
        ]
        status_choices = ['available', 'in_use', 'in_use', 'in_use', 'maintenance']
        for name, rtype in resources_data:
            Resource.objects.create(
                name=name, resource_type=rtype,
                status=random.choice(status_choices),
                assigned_to=random.choice(teams) if random.random() > 0.3 else None,
                location=random.choice([t.area for t in teams]),
                last_inspection=today - timedelta(days=random.randint(1, 90)),
            )

        # QA Checklist Forms
        from qa.models import QAChecklistForm
        from reports.models import NightReport

        qa_areas = [
            'Terminal 2 Baggage Hall - Cable tray installation',
            'Taxiway Alpha Section 3 - Resurfacing joints',
            'Cargo Area C - MEP ductwork',
            'Terminal 5 Arrivals - Ceiling grid',
            'Perimeter Road West - Drainage channel',
            'Pier 6 Gate 22 - Fire alarm cabling',
            'BHS Junction Box T2-J04 - Conveyor mounts',
        ]
        qa_outcomes = ['approved', 'approved', 'approved', 'conditional', 'approved', 'rework', 'approved']
        projects_list = list(Project.objects.all())

        for i, team in enumerate(teams[:7]):
            qa_form = QAChecklistForm.objects.create(
                team=team,
                shift_date=today,
                submitted_by=team.leader,
                area_inspected=qa_areas[i],
                project=random.choice(projects_list) if projects_list else None,
                workmanship_quality=random.choice(['pass', 'pass', 'pass', 'minor', 'pass']),
                workmanship_notes='Good finish' if random.random() > 0.5 else '',
                materials_correct=random.random() > 0.1,
                materials_stored_properly=random.random() > 0.15,
                work_to_method_statement=random.random() > 0.1,
                work_to_drawings=random.random() > 0.1,
                deviations='Minor deviation from drawing rev.C - agreed with engineer on site' if i == 3 else '',
                area_clean_tidy=random.random() > 0.2,
                waste_segregated=random.random() > 0.15,
                barriers_signage=random.random() > 0.05,
                ppe_compliant=True,
                housekeeping_notes='Debris from previous shift found in work area' if i == 5 else '',
                existing_services_protected=random.random() > 0.1,
                completed_work_protected=random.random() > 0.1,
                protection_notes='',
                snags_identified='1. Gap in cable tray support bracket\n2. Paint scuff on finished wall' if i == 5 else ('Sealant not fully cured at joint 3' if i == 3 else ''),
                snags_count=2 if i == 5 else (1 if i == 3 else 0),
                overall_outcome=qa_outcomes[i],
                inspector_comments='Satisfactory work quality' if random.random() > 0.5 else '',
                follow_up_required=(i == 5),
                follow_up_details='Rework needed on cable tray bracket - team to revisit next shift' if i == 5 else '',
            )

        # Night Report for past days
        for offset in range(7, 0, -1):
            report_date = today - timedelta(days=offset)
            NightReport.objects.create(
                date=report_date,
                generated_by=admin,
                status=random.choice(['generated', 'reviewed', 'approved']),
                total_teams=12,
                briefing_forms_submitted=random.randint(9, 12),
                qa_forms_submitted=random.randint(4, 8),
                total_staff_present=random.randint(52, 62),
                total_staff_expected=65,
                incidents_count=random.choice([0, 0, 0, 1]),
                overall_risk=random.choice(['green', 'green', 'green', 'amber']),
                manager_summary=f'Night shift {report_date.strftime("%d/%m")} completed without major issues. All teams progressing as planned.',
                handover_notes='Continue monitoring Taxiway Alpha works. Concrete pour scheduled for tomorrow night.',
            )

        self.stdout.write(self.style.SUCCESS('✓ Demo data seeded successfully!'))
        self.stdout.write(f'  Admin login: admin / admin')
        self.stdout.write(f'  {User.objects.count()} users, {Team.objects.count()} teams')
        self.stdout.write(f'  {Project.objects.count()} projects, {Task.objects.count()} tasks')
        self.stdout.write(f'  {Inspection.objects.count()} inspections, {NonConformance.objects.count()} NCRs')
        self.stdout.write(f'  {QAChecklistForm.objects.count()} QA checklist forms')
        self.stdout.write(f'  {PreBriefingForm.objects.count()} pre-briefing forms')
        self.stdout.write(f'  {NightBriefing.objects.count()} briefing sessions')
        self.stdout.write(f'  {NightReport.objects.count()} night reports')
