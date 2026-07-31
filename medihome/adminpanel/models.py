from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    TARGET_TYPES = [
        ('LAB', 'Laboratory'),
        ('HOSPITAL', 'Hospital'),
        ('DOCTOR', 'Doctor'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    target_id = models.PositiveIntegerField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def star_display(self):
        return '★' * self.rating + '☆' * (5 - self.rating)

    def __str__(self):
        return f"Review by {self.user.username} ({self.rating} Stars for {self.get_target_type_display()} ID #{self.target_id})"
