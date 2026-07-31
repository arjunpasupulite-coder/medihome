/* ==========================================================================
   MediHome - Client Validation & Interactive Scripts (Vanilla JS Only)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  console.log('MediHome initialized successfully.');

  // Auto-dismiss alert notifications after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s ease';
      setTimeout(() => alert.remove(), 500);
    }, 6000);
  });

  // Client side form validation helper for required fields
  const forms = document.querySelectorAll('form.needs-validation');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      let isValid = true;
      const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
      
      inputs.forEach(function (input) {
        if (!input.value.trim()) {
          isValid = false;
          input.classList.add('is-invalid');
          input.style.borderColor = '#ef4444';
        } else {
          input.classList.remove('is-invalid');
          input.style.borderColor = '';
        }
      });

      if (!isValid) {
        event.preventDefault();
        event.stopPropagation();
        alert('Please complete all required fields correctly before submitting.');
      }
    });
  });
});
