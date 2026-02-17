(function () {
  const actionInputs = document.querySelectorAll('input[name="action"]');
  const optionGroups = document.querySelectorAll('.options[data-action]');
  const cards = document.querySelectorAll('[data-action-card]');
  const fileInput = document.getElementById('xml-file');
  const fileName = document.getElementById('file-name');
  const serverPath = document.getElementById('server-path');
  const fileDrop = document.querySelector('.file-drop');

  function setAction(value) {
    optionGroups.forEach((group) => {
      group.hidden = group.dataset.action !== value;
    });
    cards.forEach((card) => {
      const isActive = card.dataset.actionCard === value;
      card.classList.toggle('selected', isActive);
    });
  }

  if (actionInputs.length) {
    actionInputs.forEach((input) => {
      input.addEventListener('change', () => setAction(input.value));
    });
    const checked = document.querySelector('input[name="action"]:checked');
    if (checked) {
      setAction(checked.value);
    }
  }

  if (cards.length) {
    cards.forEach((card) => {
      card.addEventListener('click', () => {
        const value = card.dataset.actionCard;
        const input = document.querySelector(`input[name="action"][value="${value}"]`);
        if (input) {
          input.checked = true;
          setAction(value);
        }
      });
    });
  }

  if (fileInput && fileName) {
    fileInput.addEventListener('change', () => {
      const name = fileInput.files && fileInput.files[0] ? fileInput.files[0].name : 'No file selected';
      fileName.textContent = name;
    });
  }

  if (serverPath && fileInput) {
    const toggleUpload = () => {
      const hasPath = serverPath.value.trim().length > 0;
      fileInput.required = !hasPath;
      fileInput.disabled = hasPath;
      if (fileDrop) {
        fileDrop.classList.toggle('disabled', hasPath);
      }
      if (fileName && hasPath) {
        fileName.textContent = 'Upload disabled (using server path)';
      } else if (fileName && !fileInput.files.length) {
        fileName.textContent = 'No file selected';
      }
    };

    serverPath.addEventListener('input', toggleUpload);
    toggleUpload();
  }
})();
