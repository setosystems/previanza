document.getElementById('select_all').addEventListener('change', function() {
    const checkboxes = document.getElementsByClassName('agent-checkbox');
    for (let checkbox of checkboxes) {
        checkbox.checked = this.checked;
    }
}); 