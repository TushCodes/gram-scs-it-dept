document.addEventListener("DOMContentLoaded", function () {
    var tableBody = document.getElementById("sheet-body");
    var saveButton = document.getElementById("save-btn");
    var addRowButton = document.getElementById("add-row-btn");
    var editModal = new bootstrap.Modal(document.getElementById("editConsignmentModal"));
    var modalSaveBtn = document.getElementById("modal-save-btn");
    var searchInput = document.getElementById("search-input");
    var perPageSelect = document.getElementById("per-page-select");
    var clearFiltersBtn = document.getElementById("clear-filters-btn");
    var prevPageBtn = document.getElementById("prev-page-btn");
    var nextPageBtn = document.getElementById("next-page-btn");
    var pageNumbersContainer = document.getElementById("page-numbers-container");

    if (!tableBody || !saveButton || !addRowButton) {
        return;
    }

    var saveUrl = tableBody.dataset.saveUrl || "";
    var listUrl = tableBody.dataset.listUrl || "";
    var deletedIds = new Set();
    var currentEditingRow = null;
    var isCreatingRow = false;
    var searchTimeout;
    var currentPage = 1;
    var currentPerPage = 10;
    var currentSearch = "";
    var currentSortBy = "id";
    var currentSortOrder = "asc";
    var totalRows = 0;
    var totalPages = 1;
    var locallyAddedRows = [];
    var modifiedRowIds = new Set();
    var newRowIdCounter = 0;

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

    function addRow(row, isLocal) {
        var source = buildRowData(row || {});
        var tr = document.createElement("tr");
        tr.dataset.id = source.id || "";
        tr.dataset.consignmentNumber = source.consignment_number || "";
        tr.dataset.row = JSON.stringify(source);
        tr.dataset.isLocal = isLocal ? "true" : "false";

        var consignmentNum = escapeHtml(source.consignment_number || "");
        var status = escapeHtml(source.status || "");
        var pickupTag = escapeHtml(source.pickup_tag || "");
        var dropPin = escapeHtml(source.drop_pincode || "");
        var pickupDate = escapeHtml(source.pickup_date || "");
        var dropEta = escapeHtml(source.drop_date || source.eta || "");

        var rowClass = isLocal ? 'table-info' : '';

        tr.innerHTML =
            "<td>" + consignmentNum + "</td>" +
            "<td>" + status + "</td>" +
            "<td>" + pickupTag + "</td>" +
            "<td>" + dropPin + "</td>" +
            "<td>" + pickupDate + "</td>" +
            "<td>" + dropEta + "</td>" +
            "<td class=\"text-center\"><button type=\"button\" class=\"btn btn-sm btn-outline-primary edit-row\" title=\"Edit\"><i class=\"fa fa-pencil\"></i></button></td>" +
            "<td class=\"text-center\"><button type=\"button\" class=\"btn btn-sm btn-outline-danger delete-row\" title=\"Delete\"><i class=\"fa fa-times\"></i></button></td>";

        if (rowClass) {
            tr.className = rowClass;
        }

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
                if (existingId && existingId > 0) {
                    deletedIds.add(existingId);
                }
                // Remove from local tracking
                var idx = locallyAddedRows.findIndex(function (r) { return r.id === existingId; });
                if (idx !== -1) {
                    locallyAddedRows.splice(idx, 1);
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
            tr.cells[0].textContent = source.consignment_number || "";
            tr.dataset.consignmentNumber = source.consignment_number || "";
            tr.cells[1].textContent = source.status || "";
            tr.dataset.row = JSON.stringify(source);
            tr.cells[2].textContent = source.pickup_tag || "";
            tr.cells[3].textContent = source.drop_pincode || "";
            tr.cells[4].textContent = source.pickup_date || "";
            tr.cells[5].textContent = source.drop_date || source.eta || "";

            // Track modification
            var rowId = tr.dataset.id ? Number(tr.dataset.id) : null;
            if (rowId && rowId > 0) {
                modifiedRowIds.add(rowId);
            }
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

        var rawRows = collectRows();
        if (!rawRows.length && deletedIds.size === 0) {
            showStatus("No changes to save.", "warning");
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
            deletedIds.clear();
            modifiedRowIds.clear();
            locallyAddedRows = [];
            newRowIdCounter = 0;
            setTimeout(function () {
                // Prefer server-provided total (after commit) to compute the
                // page that will contain newly inserted rows. Fall back to
                // an estimate using the locally tracked counts.
                try {
                    var totalAfter = (data && typeof data.total === 'number')
                        ? data.total
                        : (totalRows + (locallyAddedRows ? locallyAddedRows.length : 0) - (data.deleted_count || 0));
                    var lastPage = Math.max(1, Math.ceil(totalAfter / currentPerPage));
                    loadPage(lastPage, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
                } catch (e) {
                    loadPage(1, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
                }
            }, 1200);
        } catch (error) {
            showStatus("<strong>Save failed.</strong> " + escapeHtml(error.message || "Please check the row values and try again."), "danger");
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = "Save All";
        }
    }

    async function loadPage(page, search, perPage, sortBy, sortOrder) {
        if (!listUrl) {
            showStatus("List endpoint is missing.", "danger");
            return;
        }

        try {
            var params = new URLSearchParams({
                page: page,
                per_page: perPage,
                search: search,
                sort_by: sortBy,
                sort_order: sortOrder
            });

            showLoadingSpinner(true);

            var response = await fetch(listUrl + "?" + params.toString());
            var data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "Failed to load data.");
            }

            // Clear existing rows
            tableBody.innerHTML = "";

            // Add fetched rows
            data.rows.forEach(function (row) {
                addRow(row, false);
            });

            // Update pagination info
            totalRows = data.total;
            totalPages = data.pages;
            currentPage = page;
            currentPerPage = perPage;
            currentSearch = search;
            currentSortBy = sortBy;
            currentSortOrder = sortOrder;

            updatePaginationUI();
            updateSortHeaders();

        } catch (error) {
            showStatus("<strong>Failed to load data.</strong> " + escapeHtml(error.message || "Please try again."), "danger");
        } finally {
            showLoadingSpinner(false);
        }
    }

    function updatePaginationUI() {
        var showingStart = (currentPage - 1) * currentPerPage + 1;
        var showingEnd = Math.min(currentPage * currentPerPage, totalRows);

        document.getElementById("showing-start").textContent = totalRows > 0 ? showingStart : 0;
        document.getElementById("showing-end").textContent = showingEnd;
        document.getElementById("total-count").textContent = totalRows;

        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;

        // Generate page numbers
        pageNumbersContainer.innerHTML = "";
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            var firstPageBtn = document.createElement("button");
            firstPageBtn.type = "button";
            firstPageBtn.className = "btn btn-outline-secondary btn-sm page-number";
            firstPageBtn.textContent = "1";
            firstPageBtn.addEventListener("click", function () {
                loadPage(1, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
            });
            pageNumbersContainer.appendChild(firstPageBtn);

            if (startPage > 2) {
                var ellipsis = document.createElement("span");
                ellipsis.className = "page-number";
                ellipsis.textContent = "...";
                pageNumbersContainer.appendChild(ellipsis);
            }
        }

        for (var i = startPage; i <= endPage; i++) {
            var pageBtn = document.createElement("button");
            pageBtn.type = "button";
            pageBtn.className = "btn btn-sm page-number";
            if (i === currentPage) {
                pageBtn.className += " btn-primary";
                pageBtn.disabled = true;
            } else {
                pageBtn.className += " btn-outline-secondary";
            }
            pageBtn.textContent = i;
            pageBtn.addEventListener("click", function (page) {
                return function () {
                    loadPage(page, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
                };
            }(i));
            pageNumbersContainer.appendChild(pageBtn);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                var ellipsis2 = document.createElement("span");
                ellipsis2.className = "page-number";
                ellipsis2.textContent = "...";
                pageNumbersContainer.appendChild(ellipsis2);
            }

            var lastPageBtn = document.createElement("button");
            lastPageBtn.type = "button";
            lastPageBtn.className = "btn btn-outline-secondary btn-sm page-number";
            lastPageBtn.textContent = totalPages;
            lastPageBtn.addEventListener("click", function () {
                loadPage(totalPages, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
            });
            pageNumbersContainer.appendChild(lastPageBtn);
        }
    }

    function updateSortHeaders() {
        var headers = document.querySelectorAll(".sort-header");
        headers.forEach(function (header) {
            var icon = header.querySelector(".sort-icon i");
            var column = header.dataset.sortColumn;
            if (column === currentSortBy) {
                icon.className = currentSortOrder === "asc" ? "fa fa-sort-up" : "fa fa-sort-down";
                header.querySelector(".sort-icon").classList.add("active");
            } else {
                icon.className = "fa fa-sort";
                header.querySelector(".sort-icon").classList.remove("active");
            }
        });
    }

    function showLoadingSpinner(show) {
        var spinner = document.getElementById("loading-spinner");
        if (show) {
            spinner.classList.remove("d-none");
        } else {
            spinner.classList.add("d-none");
        }
    }

    // Event Listeners
    modalSaveBtn.addEventListener("click", function () {
        if (isCreatingRow) {
            var newId = -(++newRowIdCounter);
            var newSource = buildRowData({}, newId);
            if (updateRowFromModal(null, newSource)) {
                locallyAddedRows.push(newSource);
                addRow(newSource, true);
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

    // Search with debouncing
    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
            loadPage(1, searchInput.value.trim(), currentPerPage, currentSortBy, currentSortOrder);
        }, 500);
    });

    // Per-page selector
    perPageSelect.addEventListener("change", function () {
        currentPerPage = parseInt(perPageSelect.value);
        loadPage(1, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
    });

    // Clear filters
    clearFiltersBtn.addEventListener("click", function () {
        searchInput.value = "";
        perPageSelect.value = "10";
        currentPerPage = 10;
        currentSearch = "";
        loadPage(1, "", 10, "id", "asc");
    });

    // Pagination buttons
    prevPageBtn.addEventListener("click", function () {
        if (currentPage > 1) {
            loadPage(currentPage - 1, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
        }
    });

    nextPageBtn.addEventListener("click", function () {
        if (currentPage < totalPages) {
            loadPage(currentPage + 1, currentSearch, currentPerPage, currentSortBy, currentSortOrder);
        }
    });

    // Sort headers
    var sortHeaders = document.querySelectorAll(".sort-header");
    sortHeaders.forEach(function (header) {
        header.addEventListener("click", function () {
            var column = header.dataset.sortColumn;
            var newOrder = "asc";
            if (currentSortBy === column && currentSortOrder === "asc") {
                newOrder = "desc";
            }
            loadPage(1, currentSearch, currentPerPage, column, newOrder);
        });
    });

    // Initial load: prefer server-rendered `data-existing-rows` when present
    (function initialLoad() {
        var existingJson = tableBody.dataset.existingRows || "";
        if (existingJson) {
            try {
                var existingRows = JSON.parse(existingJson || "[]") || [];
                if (existingRows.length) {
                    tableBody.innerHTML = "";
                    existingRows.forEach(function (row) { addRow(row, false); });
                    totalRows = existingRows.length;
                    totalPages = Math.max(1, Math.ceil(totalRows / currentPerPage));
                    currentPage = 1;
                    updatePaginationUI();
                    updateSortHeaders();
                    return;
                }
            } catch (e) {
                // Fall through to API load on parse error
            }
        }

        // Fallback to paginated API load
        loadPage(1, "", currentPerPage, currentSortBy, currentSortOrder);
    })();
});

