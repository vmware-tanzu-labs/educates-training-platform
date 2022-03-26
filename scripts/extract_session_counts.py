import csv

from workshops.models import (TrainingPortal, Workshop,
        SessionState, Session, Environment)

environments = Environment.objects.all()

with open('session-counts.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Workshop', 'Sessions'])
    for environment in environments:
        count = Session.objects.filter(
                environment__name=environment.name,
                state=SessionState.STOPPED).count()
        writer.writerow([environment.workshop.name, count])
