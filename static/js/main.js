// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化所有弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 表单验证
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 自动隐藏警告消息
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 文件上传预览
    var fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            var fileName = e.target.files[0].name;
            var fileLabel = e.target.nextElementSibling;
            if (fileLabel) {
                fileLabel.textContent = fileName;
            }
        });
    }

    // 表格排序
    var tables = document.querySelectorAll('table.sortable');
    tables.forEach(function(table) {
        var headers = table.querySelectorAll('th');
        headers.forEach(function(header) {
            header.addEventListener('click', function() {
                var index = Array.from(header.parentElement.children).indexOf(header);
                sortTable(table, index);
            });
        });
    });
});

// 表格排序函数
function sortTable(table, column) {
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var direction = table.dataset.sortDirection === 'asc' ? -1 : 1;
    
    rows.sort(function(a, b) {
        var aValue = a.children[column].textContent.trim();
        var bValue = b.children[column].textContent.trim();
        
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return direction * (parseFloat(aValue) - parseFloat(bValue));
        }
        return direction * aValue.localeCompare(bValue);
    });
    
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
    
    table.dataset.sortDirection = direction === 1 ? 'asc' : 'desc';
}

// 导出数据为Excel
function exportToExcel(tableId, filename) {
    var table = document.getElementById(tableId);
    var wb = XLSX.utils.table_to_book(table, {sheet: "Sheet JS"});
    XLSX.writeFile(wb, filename);
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('复制成功');
    }).catch(function() {
        showToast('复制失败，请手动复制');
    });
}

// 显示提示消息
function showToast(message) {
    var toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">提示</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    var bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        document.body.removeChild(toast);
    });
} 