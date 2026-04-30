document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('pickup-station-form');
  var table = document.getElementById('pickup-stations-table');
  var inputId = document.getElementById('station-id');
  var inputName = document.getElementById('station-name');
  var inputPin = document.getElementById('station-pin');
  var inputAddress = document.getElementById('station-address');
  var btnCancel = document.getElementById('station-cancel');

  function resetForm() {
    inputId.value = '';
    inputName.value = '';
    inputPin.value = '';
    inputAddress.value = '';
    inputName.focus();
  }

  async function refreshList() {
    var resp = await fetch('/master/pickup-stations/list');
    if (!resp.ok) return;
    var names = await resp.json();
    // simple reload page to reflect server-side list
    window.location.reload();
  }

  table.addEventListener('click', async function (e) {
    var tr = e.target.closest('tr');
    if (!tr) return;
    var id = tr.dataset.id;

    if (e.target.classList.contains('edit')) {
      inputId.value = id;
      inputName.value = tr.querySelector('.name').textContent.trim();
      inputPin.value = tr.querySelector('.pin').textContent.trim();
      inputAddress.value = tr.querySelector('.address').textContent.trim();
      inputName.focus();
    }

    if (e.target.classList.contains('delete')) {
      if (!confirm('Delete station?')) return;
      var resp = await fetch('/master/pickup-stations/' + id, { method: 'DELETE' });
      if (resp.ok) {
        tr.remove();
      } else {
        var data = await resp.json().catch(() => ({}));
        alert(data.message || 'Failed to delete');
      }
    }
  });

  btnCancel.addEventListener('click', function () {
    resetForm();
  });

  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var id = inputId.value && Number(inputId.value);
    var payload = {
      name: inputName.value.trim(),
      pin_code: inputPin.value.trim(),
      address: inputAddress.value.trim(),
    };

    try {
      var resp;
      if (id) {
        resp = await fetch('/master/pickup-stations/' + id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } else {
        resp = await fetch('/master/pickup-stations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      var data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.success) {
        alert(data.message || 'Failed to save station');
        return;
      }

      // reload to update table
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert('Failed to save station');
    }
  });
});
