// script.js
// Функция для обработки подтверждения удаления пользователя
function confirmDelete(id, name) {
    if (confirm('Вы уверены, что хотите удалить пользователя ' + name + '?')) {
        document.getElementById('delete-form-' + id).submit();
    }
    return false;
}

// Валидация формы на стороне клиента
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
});