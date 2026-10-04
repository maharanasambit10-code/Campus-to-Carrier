from django.db import models
from companies.models import Company
from jobs.models import Job


class PlacementDrive(models.Model):
	STATUS_CHOICES = (
		('PLANNED', 'Planned'),
		('OPEN', 'Open'),
		('CLOSED', 'Closed'),
	)

	title = models.CharField(max_length=200)
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='placement_drives')
	jobs = models.ManyToManyField(Job, blank=True, related_name='placement_drives')
	start_date = models.DateField()
	end_date = models.DateField()
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANNED')
	coordinator_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-start_date']

	def __str__(self):
		return f'{self.title} - {self.company.name}'
