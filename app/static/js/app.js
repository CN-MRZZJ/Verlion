(function () {
  function showMsg(text, ok) {
    if (window.layui && layui.layer) {
      layui.layer.msg(text, { icon: ok ? 1 : 2, time: 1800 });
      return;
    }
    alert(text);
  }

  function bindAjaxForms() {
    var forms = document.querySelectorAll('form[data-ajax="true"], form.js-ajax-form');
    forms.forEach(function (form) {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();
        var submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        try {
          var resp = await fetch(form.action, {
            method: (form.method || 'POST').toUpperCase(),
            body: new FormData(form)
          });
          var data = await resp.json();
          if (!resp.ok || data.ok === false) {
            showMsg(data.error || '提交失败', false);
            return;
          }

          form.dispatchEvent(new CustomEvent('ajax:success', { detail: data }));

          var summary = [];
          if (typeof data.inserted !== 'undefined') summary.push('新增 ' + data.inserted);
          if (typeof data.skipped !== 'undefined') summary.push('跳过 ' + data.skipped);
          if (Array.isArray(data.errors) && data.errors.length > 0) summary.push('错误 ' + data.errors.length);
          if (Array.isArray(data.skipped_details) && data.skipped_details.length > 0) summary.push('跳过明细 ' + data.skipped_details.length);
          showMsg(summary.length > 0 ? ('操作成功：' + summary.join('，')) : '操作成功', true);

          var detailParts = [];
          if (Array.isArray(data.errors) && data.errors.length > 0) {
            detailParts.push('【错误明细】\n' + data.errors.join('\n'));
          }
          if (Array.isArray(data.skipped_details) && data.skipped_details.length > 0) {
            detailParts.push('【跳过明细】\n' + data.skipped_details.join('\n'));
          }

          if (detailParts.length > 0) {
            var detailText = detailParts.join('\n\n');
            if (window.layui && layui.layer) {
              layui.layer.open({
                type: 1,
                title: '导入反馈明细',
                area: ['760px', '460px'],
                shadeClose: true,
                content: '<div style="padding:12px;white-space:pre-wrap;line-height:1.55;max-height:390px;overflow:auto;">'
                  + detailText.replace(/</g, '&lt;').replace(/>/g, '&gt;')
                  + '</div>'
              });
            } else {
              alert(detailText);
            }
          } else {
            var noReload = (form.getAttribute('data-no-reload') || '') === '1';
            if (!noReload) {
              setTimeout(function () {
                window.location.reload();
              }, 800);
            }
          }
        } catch (err) {
          showMsg('请求异常: ' + err, false);
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    });
  }

  function getQueryObjFromForm(form) {
    var fd = new FormData(form);
    var obj = {};
    fd.forEach(function (value, key) {
      obj[key] = String(value || '').trim();
    });
    return obj;
  }

  function renderTable(columns, items, sortState, onSortClick) {
    var head = document.getElementById('grid-head');
    var body = document.getElementById('grid-body');
    if (!head || !body) return;

    var headHtml = '<tr>' + columns.map(function (c) {
      var active = sortState && sortState.sort_by === c;
      var arrow = active ? (sortState.sort_dir === 'asc' ? ' ▲' : ' ▼') : '';
      return '<th><a href="#" class="js-sort-head" data-col="' + c + '">' + c + arrow + '</a></th>';
    }).join('') + '</tr>';
    head.innerHTML = headHtml;
    head.querySelectorAll('.js-sort-head').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof onSortClick === 'function') onSortClick(a.getAttribute('data-col') || '');
      });
    });

    var rowsHtml = items.map(function (row) {
      return '<tr>' + columns.map(function (c) {
        var v = row[c];
        return '<td>' + (v === null || typeof v === 'undefined' ? '' : String(v)) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    body.innerHTML = rowsHtml || '<tr><td colspan="' + (columns.length || 1) + '">暂无数据</td></tr>';
  }

  function initDataCenter() {
    var app = document.getElementById('data-center-app');
    if (!app) return;

    var form = document.getElementById('grid-filter-form');
    var btnSearch = document.getElementById('btn-search');
    var btnReset = document.getElementById('btn-reset');
    var btnRefresh = document.getElementById('btn-refresh');
    var btnExport = document.getElementById('btn-export');
    var meta = document.getElementById('grid-meta');
    var metricView = document.getElementById('dc-metric-view');
    var metricTotal = document.getElementById('dc-metric-total');
    var metricPage = document.getElementById('dc-metric-page');
    var metricSort = document.getElementById('dc-metric-sort');
    var state = {
      page: 1,
      page_size: 20,
      sort_by: '',
      sort_dir: 'desc'
    };

    function setActiveView(view) {
      var viewInput = document.getElementById('view-select');
      if (viewInput) viewInput.value = view;
      app.querySelectorAll('.dc-view-btn').forEach(function (btn) {
        if ((btn.getAttribute('data-view') || '') === view) btn.classList.add('is-active');
        else btn.classList.remove('is-active');
      });
    }

    function saveState(filters) {
      var payload = Object.assign({}, filters, {
        page: state.page,
        page_size: state.page_size,
        sort_by: state.sort_by,
        sort_dir: state.sort_dir
      });
      localStorage.setItem('sports_point_grid_state', JSON.stringify(payload));
    }

    function loadState() {
      try {
        var raw = localStorage.getItem('sports_point_grid_state');
        if (!raw) return;
        var s = JSON.parse(raw);
        Object.keys(s).forEach(function (k) {
          var input = form.querySelector('[name="' + k + '"]');
          if (input) input.value = s[k];
        });
        if (s.page) state.page = Number(s.page) || 1;
        if (s.page_size) state.page_size = Number(s.page_size) || 20;
        state.sort_by = String(s.sort_by || '');
        state.sort_dir = String(s.sort_dir || 'desc');
        if (s.view) setActiveView(String(s.view));
      } catch (_) {}
    }

    async function fetchGrid(jumpFromPagination) {
      var filters = getQueryObjFromForm(form);
      state.page_size = Number(filters.page_size || state.page_size || 20);
      if (!jumpFromPagination) state.page = 1;

      var view = filters.view || 'events';
      var qs = new URLSearchParams({
        page: String(state.page),
        page_size: String(state.page_size),
        keyword: filters.keyword || '',
        department_name: filters.department_name || '',
        gender: filters.gender || '',
        age_group: filters.age_group || '',
        category: filters.category || '',
        scoring_strategy: filters.scoring_strategy || '',
        sort_by: state.sort_by || '',
        sort_dir: state.sort_dir || 'desc'
      });

      var resp = await fetch('/api/data/' + encodeURIComponent(view) + '?' + qs.toString());
      var data = await resp.json();
      if (!resp.ok || data.ok === false) {
        showMsg(data.error || '查询失败', false);
        return;
      }

      state.sort_by = String(data.sort_by || state.sort_by || '');
      state.sort_dir = String(data.sort_dir || state.sort_dir || 'desc');
      renderTable(
        data.columns || [],
        data.items || [],
        { sort_by: state.sort_by, sort_dir: state.sort_dir },
        function (col) {
          if (!col) return;
          if (state.sort_by === col) {
            state.sort_dir = state.sort_dir === 'asc' ? 'desc' : 'asc';
          } else {
            state.sort_by = col;
            state.sort_dir = 'asc';
          }
          state.page = 1;
          fetchGrid(true);
        }
      );
      meta.textContent = '当前视图：' + data.view + '，总记录：' + data.total + '，第 ' + data.page + '/' + (data.pages || 1) + ' 页';
      if (metricView) metricView.textContent = String(data.view || '-');
      if (metricTotal) metricTotal.textContent = String(data.total || 0);
      if (metricPage) metricPage.textContent = String(data.page || 1) + '/' + String(data.pages || 1);
      if (metricSort) {
        metricSort.textContent = state.sort_by
          ? (state.sort_by + ' ' + (state.sort_dir === 'asc' ? '升序' : '降序'))
          : '默认';
      }

      if (window.layui && layui.laypage) {
        layui.laypage.render({
          elem: 'grid-pagination',
          count: data.total || 0,
          curr: data.page || 1,
          limit: data.page_size || 20,
          limits: [20, 50, 100],
          layout: ['count', 'prev', 'page', 'next', 'limit', 'skip'],
          jump: function (obj, first) {
            if (first) return;
            state.page = obj.curr;
            state.page_size = obj.limit;
            var ps = form.querySelector('[name="page_size"]');
            if (ps) ps.value = String(obj.limit);
            fetchGrid(true);
          }
        });
      }

      saveState(filters);
    }

    btnSearch.addEventListener('click', function () {
      fetchGrid(false);
    });

    if (btnReset) {
      btnReset.addEventListener('click', function () {
        form.reset();
        var ps = form.querySelector('[name="page_size"]');
        if (ps) ps.value = '20';
        state.page = 1;
        state.page_size = 20;
        state.sort_by = '';
        state.sort_dir = 'desc';
        localStorage.removeItem('sports_point_grid_state');
        if (window.layui && layui.form) layui.form.render('select');
        fetchGrid(false);
      });
    }

    if (btnRefresh) {
      btnRefresh.addEventListener('click', function () {
        fetchGrid(true);
      });
    }

    if (btnExport) {
      btnExport.addEventListener('click', function () {
        var filters = getQueryObjFromForm(form);
        var view = filters.view || 'events';
        var qs = new URLSearchParams({
          keyword: filters.keyword || '',
          department_name: filters.department_name || '',
          gender: filters.gender || '',
          age_group: filters.age_group || '',
          category: filters.category || '',
          scoring_strategy: filters.scoring_strategy || ''
        });
        window.open('/export/data/' + encodeURIComponent(view) + '?' + qs.toString(), '_blank');
      });
    }

    var viewSelect = document.getElementById('view-select');
    if (viewSelect) setActiveView(viewSelect.value || 'events');
    app.querySelectorAll('.dc-view-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var view = btn.getAttribute('data-view') || '';
        if (!view) return;
        setActiveView(view);
        state.sort_by = '';
        state.sort_dir = 'desc';
        fetchGrid(false);
      });
    });

    loadState();
    var initialView = (viewSelect && viewSelect.value) ? viewSelect.value : 'events';
    setActiveView(initialView);
    fetchGrid(true);
  }

  function initClearDataGuard() {
    var form = document.getElementById('clear-data-form');
    if (!form) return;
    var hint = document.getElementById('clear-code-hint');

    function selectedCount() {
      return form.querySelectorAll('input[name="tables"]:checked').length;
    }

    function refreshHint() {
      var code = 'CLEAR-' + String(selectedCount());
      if (hint) hint.textContent = code;
    }

    form.addEventListener('change', function (e) {
      if (e.target && e.target.name === 'tables') refreshHint();
    });

    form.addEventListener('submit', function (e) {
      var n = selectedCount();
      if (n <= 0) {
        e.preventDefault();
        showMsg('请先选择至少一张要清除的表', false);
        return;
      }
      var ok = window.confirm('即将清除 ' + n + ' 张表的数据，此操作不可恢复。是否继续？');
      if (!ok) e.preventDefault();
    });

    refreshHint();
  }

  if (window.layui) {
    layui.use(['form', 'laypage', 'layer'], function () {
      initClearDataGuard();
      bindAjaxForms();
      initDataCenter();
      layui.form.render();
    });
  } else {
    initClearDataGuard();
    bindAjaxForms();
    initDataCenter();
  }
})();
