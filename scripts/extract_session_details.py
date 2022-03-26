import csv

from workshops.models import (TrainingPortal, Workshop,
        SessionState, Session, Environment)

sessions = Session.objects.filter(state=SessionState.STOPPED)

with open('session-details.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Workshop', 'Session', 'Created', 'Started', 'Ended'])
    for session in sessions:
        created = session.created
        finished = session.expires
        started = session.started or finished
        format = "%d/%m/%Y %H:%M:%S"
        writer.writerow([session.environment.workshop.name,
            session.name, created.strftime(format),
            started.strftime(format), finished.strftime(format)])
