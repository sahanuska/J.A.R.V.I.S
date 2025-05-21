document.addEventListener('DOMContentLoaded', function() {
  const registerForm = document.querySelector('.auth-form');
  const passwordInput = document.getElementById('access_code');
  const confirmPasswordInput = document.getElementById('confirm_code');
  
  if (registerForm) {
      registerForm.addEventListener('submit', async function(e) {
          e.preventDefault();
          
          // Get form values
          const agentId = document.getElementById('agent_id').value.trim();
          const email = document.getElementById('security_email').value.trim();
          const password = passwordInput.value;
          const confirmPassword = confirmPasswordInput.value;
          
          // Clear previous errors
          clearErrorMessages();
          
          // Validate fields
          let isValid = true;
          
          if (!agentId) {
              showError('agent_id', 'Agent ID is required');
              isValid = false;
          } else if (agentId.length < 4) {
              showError('agent_id', 'Agent ID must be at least 4 characters');
              isValid = false;
          }
          
          if (!email) {
              showError('security_email', 'Security email is required');
              isValid = false;
          } else if (!validateEmail(email)) {
              showError('security_email', 'Please enter a valid security email');
              isValid = false;
          }
          
          if (!password) {
              showError('access_code', 'Access code is required');
              isValid = false;
          } else if (password.length < 8) {
              showError('access_code', 'Access code must be at least 8 characters');
              isValid = false;
          }
          
          if (!confirmPassword) {
              showError('confirm_code', 'Please confirm your access code');
              isValid = false;
          } else if (password !== confirmPassword) {
              showError('confirm_code', 'Access codes do not match');
              isValid = false;
          }
          
          if (!isValid) return;
          
          // Submit form
          try {
              const submitBtn = registerForm.querySelector('button[type="submit"]');
              submitBtn.disabled = true;
              submitBtn.textContent = 'SECURING ACCESS...';
              
              // Simulate API call (replace with actual fetch in production)
              await new Promise(resolve => setTimeout(resolve, 1500));
              
              // Show success and redirect
              showSuccessMessage('CLEARANCE GRANTED! Redirecting to access portal...');
              setTimeout(() => {
                  window.location.href = '/login';
              }, 2000);
              
          } catch (error) {
              console.error('Registration error:', error);
              showFormError('System error. Please try again.');
              const submitBtn = registerForm.querySelector('button[type="submit"]');
              submitBtn.disabled = false;
              submitBtn.textContent = 'REQUEST CLEARANCE';
          }
      });
  }
  
  // Helper functions
  function clearErrorMessages() {
      document.querySelectorAll('.error-message').forEach(el => el.remove());
  }
  
  function showError(fieldId, message) {
      const field = document.getElementById(fieldId);
      const errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.textContent = message;
      errorElement.style.color = '#ff4444';
      errorElement.style.marginTop = '5px';
      errorElement.style.fontSize = '0.8rem';
      
      field.parentNode.appendChild(errorElement);
  }
  
  function showFormError(message) {
      const errorElement = document.createElement('div');
      errorElement.className = 'form-error-message';
      errorElement.textContent = message;
      errorElement.style.color = '#ff4444';
      errorElement.style.textAlign = 'center';
      errorElement.style.margin = '15px 0';
      
      // Insert before the submit button
      registerForm.insertBefore(errorElement, registerForm.querySelector('button[type="submit"]'));
  }
  
  function showSuccessMessage(message) {
      const successElement = document.createElement('div');
      successElement.className = 'success-message';
      successElement.textContent = message;
      successElement.style.color = '#00C851';
      successElement.style.textAlign = 'center';
      successElement.style.margin = '15px 0';
      successElement.style.fontWeight = 'bold';
      
      // Insert before the submit button
      registerForm.insertBefore(successElement, registerForm.querySelector('button[type="submit"]'));
  }
  
  function validateEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email);
  }
});
