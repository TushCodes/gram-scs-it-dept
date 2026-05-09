document.addEventListener("DOMContentLoaded", function () {
    var tableBody = document.getElementById("sheet-body");
    var saveButton = document.getElementById("save-btn");
    var addRowButton = document.getElementById("add-row-btn");
    var editModal = new bootstrap.Modal(document.getElementById("editConsignmentModal"));
    var modalSaveBtn = document.getElementById("modal-save-btn");

    if (!tableBody || !saveButton || !addRowButton) {
        return;
    }

    var saveUrl = tableBody.dataset.saveUrl || "";
    var existingRows = [];
    var deletedIds = new Set();
    var currentEditingRow = null; // Track which row is being edited
    var isCreatingRow = false;

    try {
        existingRows = JSON.parse(tableBody.dataset.existingRows || "[]");
    } catch (error) {
        console.error("Failed to parse existing consignment rows.", error);
    }

    function showStatus(message, type) {
        var el = document.getElementById("status-msg");
        if (!el) {
            return;
        }
        el.innerHTML = message;
        el.className = "alert alert-" + type + " shadow-sm border-0";
        el.classList.remove("d-none");
        el.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function escapeHtml(text) {
        return String(text == null ? "" : text)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function validatePincode(value) {
        var raw = (value || "").trim();
        if (raw === "") {
            return true; // Allow empty
        }
        if (!/^[1-9][0-9]{5}$/.test(raw)) {
            return false;
        }
        return true;
    }

    function normalizePincode(value) {
        var raw = (value || "").trim();
        if (raw === "") {
            return "";
        }
        return raw;
    }

    function populateModal(row) {
        var consInput = document.getElementById("modal-consignment-number");
        consInput.value = row.consignment_number || "";
        // Ensure the input is editable (some scripts may toggle readOnly)
        try {
            consInput.readOnly = false;
        } catch (e) {
            // ignore
        }
        consInput.focus();
        document.getElementById("modal-status").value = row.status || "";
        document.getElementById("modal-pickup-address").value = row.pickup_address || "";
        document.getElementById("modal-pickup-pincode").value = row.pickup_pincode || "";
        document.getElementById("modal-pickup-tag").value = row.pickup_tag || "";
        document.getElementById("modal-pickup-date").value = row.pickup_date || "";
        document.getElementById("modal-drop-address").value = row.drop_address || "";
        document.getElementById("modal-drop-pincode").value = row.drop_pincode || "";
        document.getElementById("modal-drop-tag").value = row.drop_tag || "";
        document.getElementById("modal-drop-date").value = row.drop_date || "";
    }

    function clearModal() {
        populateModal({
            consignment_number: "",
            status: "",
            pickup_address: "",
            pickup_pincode: "",
            pickup_tag: "",
            pickup_date: "",
            drop_address: "",
            drop_pincode: "",
            drop_tag: "",
            drop_date: "",
            eta: ""
        });
    }

    function buildRowData(source, fallbackId) {
        var data = source || {};
        return {
            id: data.id || fallbackId || null,
            consignment_number: data.consignment_number || "",
            status: data.status || "",
            pickup_address: data.pickup_address || "",
            pickup_pincode: data.pickup_pincode || "",
            pickup_tag: data.pickup_tag || "",
            pickup_date: data.pickup_date || "",
            drop_address: data.drop_address || "",
            drop_pincode: data.drop_pincode || "",
            drop_tag: data.drop_tag || "",
            drop_date: data.drop_date || "",
            eta: data.eta || ""
        };
    }

    function getRowDataFromTr(tr) {
        try {
            return buildRowData(JSON.parse(tr.dataset.row || "{}"), tr.dataset.id ? Number(tr.dataset.id) : null);
        } catch (error) {
            return buildRowData({}, tr.dataset.id ? Number(tr.dataset.id) : null);
        }
    }

    function addRow(row) {
        var source = buildRowData(row || {});
        var tr = document.createElement("tr");
        tr.dataset.id = source.id || "";
        tr.dataset.consignmentNumber = source.consignment_number || "";
        tr.dataset.row = JSON.stringify(source);

        var consignmentNum = escapeHtml(source.consignment_number || "");
        var status = escapeHtml(source.status || "");
        var pickupTag = escapeHtml(source.pickup_tag || "");
        var dropPin = escapeHtml(source.drop_pincode || "");
        var pickupDate = escapeHtml(source.pickup_date || "");
        var dropEta = escapeHtml(source.drop_date || source.eta || "");

        tr.innerHTML =
            "<td>" + consignmentNum + "</td>" +
            "<td>" + status + "</td>" +
            "<td>" + pickupTag + "</td>" +
            "<td>" + dropPin + "</td>" +
            "<td>" + pickupDate + "</td>" +
            "<td>" + dropEta + "</td>" +
            "<td class=\"text-center\"><button type=\"button\" class=\"btn btn-sm btn-outline-primary edit-row\" title=\"Edit\"><i class=\"fa fa-pencil\"></i></button></td>" +
            "<td class=\"text-center\"><button type=\"button\" class=\"btn btn-sm btn-outline-danger delete-row\" title=\"Delete\"><i class=\"fa fa-times\"></i></button></td>";

        var editButton = tr.querySelector(".edit-row");
        if (editButton) {
            editButton.addEventListener("click", function () {
                isCreatingRow = false;
                currentEditingRow = tr;
                populateModal(getRowDataFromTr(tr));
                editModal.show();
            });
        }

        var deleteButton = tr.querySelector(".delete-row");
        if (deleteButton) {
            deleteButton.addEventListener("click", function () {
                var existingId = tr.dataset.id ? Number(tr.dataset.id) : null;
                if (existingId) {
                    deletedIds.add(existingId);
                }
                tr.remove();
            });
        }

        tableBody.appendChild(tr);
    }

    function updateRowFromModal(tr, source) {
        var consignmentNumber = document.getElementById("modal-consignment-number").value.trim();
        var status = document.getElementById("modal-status").value.trim();
        var pickupPincode = document.getElementById("modal-pickup-pincode").value.trim();
        var dropPincode = document.getElementById("modal-drop-pincode").value.trim();

        if (!consignmentNumber) {
            showStatus("Consignment number cannot be empty.", "danger");
            return false;
        }

        if (!validatePincode(pickupPincode)) {
            showStatus("Pickup Pincode must be a valid 6-digit number or empty.", "danger");
            return false;
        }
        if (!validatePincode(dropPincode)) {
            showStatus("Drop Pincode must be a valid 6-digit number or empty.", "danger");
            return false;
        }

        // Update source object
        source.consignment_number = consignmentNumber;
        source.status = status;
        source.pickup_address = document.getElementById("modal-pickup-address").value.trim();
        source.pickup_pincode = normalizePincode(pickupPincode);
        source.pickup_tag = document.getElementById("modal-pickup-tag").value.trim();
        source.pickup_date = document.getElementById("modal-pickup-date").value.trim();
        source.drop_address = document.getElementById("modal-drop-address").value.trim();
        source.drop_pincode = normalizePincode(dropPincode);
        source.drop_tag = document.getElementById("modal-drop-tag").value.trim();
        source.drop_date = document.getElementById("modal-drop-date").value.trim();

        if (tr) {
            // Update table row display and dataset
            tr.cells[0].textContent = source.consignment_number || "";
            tr.dataset.consignmentNumber = source.consignment_number || "";
            tr.cells[1].textContent = source.status || "";
            tr.dataset.row = JSON.stringify(source);
            tr.cells[2].textContent = source.pickup_tag || "";
            tr.cells[3].textContent = source.drop_pincode || "";
            tr.cells[4].textContent = source.pickup_date || "";
            tr.cells[5].textContent = source.drop_date || source.eta || "";
        }

        return true;
    }

    function collectRows() {
        var rows = [];
        var tableRows = document.querySelectorAll("#sheet-body tr");

        tableRows.forEach(function (tr) {
            var rowData = getRowDataFromTr(tr);
            if (rowData.consignment_number && rowData.consignment_number.trim()) {
                rows.push(rowData);
            }
        });

        return rows;
    }

    async function saveSheet() {
        if (!saveUrl) {
            showStatus("Save endpoint is missing.", "danger");
            return;
        }

        // Collect all row data from row dataset (single source of truth)
        var rawRows = collectRows();
        if (!rawRows.length && deletedIds.size === 0) {
            showStatus("Sheet is empty. Add at least one row.", "warning");
            return;
        }

        try {
            saveButton.disabled = true;
            var originalButtonText = saveButton.textContent;
            saveButton.textContent = "Saving...";
            showStatus('<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving rows to database...', "info");

            var response = await fetch(saveUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    rows: rawRows,
                    deleted_ids: Array.from(deletedIds)
                })
            });

            if (response.status === 401) {
                throw new Error("Your session has expired. Please refresh the page and log in again.");
            }

            var data;
            try {
                data = await response.json();
            } catch (parseError) {
                throw new Error("Invalid response from server. Please check your connection and try again.");
            }

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Save failed.");
            }

            showStatus("<strong>Saved successfully.</strong> Your internal database has been updated.", "success");
            setTimeout(function () {
                window.location.reload();
            }, 1200);
        } catch (error) {
            showStatus("<strong>Save failed.</strong> " + escapeHtml(error.message || "Please check the row values and try again."), "danger");
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = "Save All";
        }
    }

    // Modal save button handler
    modalSaveBtn.addEventListener("click", function () {
        if (isCreatingRow) {
            var newSource = buildRowData({});
            if (updateRowFromModal(null, newSource)) {
                addRow(newSource);
                editModal.hide();
                currentEditingRow = null;
                isCreatingRow = false;
            }
            return;
        }

        if (currentEditingRow) {
            var source = getRowDataFromTr(currentEditingRow);

            if (updateRowFromModal(currentEditingRow, source)) {
                editModal.hide();
                currentEditingRow = null;
                isCreatingRow = false;
            }
        }
    });

    addRowButton.addEventListener("click", function () {
        isCreatingRow = true;
        currentEditingRow = null;
        clearModal();
        editModal.show();
    });

    document.getElementById("editConsignmentModal").addEventListener("hidden.bs.modal", function () {
        currentEditingRow = null;
        isCreatingRow = false;
        clearModal();
    });

    saveButton.addEventListener("click", saveSheet);

    if (existingRows.length) {
        existingRows.forEach(addRow);
    }
});

