(() => {
  const app = window.CampusConnect;
  const shell = document.querySelector('.app-shell');
  if (!shell) return;
  const role = shell.dataset.role;
  document.querySelectorAll('[data-admin-only]').forEach(el => { if (!['admin','placement_officer'].includes(role)) el.hidden = true; });
  document.querySelectorAll('[data-manage-only]').forEach(el => { if (!['admin','placement_officer','faculty'].includes(role)) el.hidden = true; });
  document.querySelectorAll('[data-roles]').forEach(el => { if (!el.dataset.roles.split(',').includes(role)) el.hidden = true; });
  const metrics = document.getElementById('metrics');
  const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function cards(items) { metrics.innerHTML = items.map(([label,value]) => `<article class="metric-card"><div class="metric-label">${esc(label)}</div><div class="metric-value">${esc(value)}</div></article>`).join(''); }
  function table(headings, rows) {
    if (!rows.length) return '<div class="empty-note">Nothing here yet. New activity will appear as your campus records grow.</div>';
    return `<table class="table"><thead><tr>${headings.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(x=>`<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }
  const studentSearch=document.getElementById('student-search');
  if (studentSearch) studentSearch.addEventListener('submit',async event=>{
    event.preventDefault();
    const query=new URLSearchParams(new FormData(studentSearch));
    for (const [key,value] of [...query.entries()]) if (!value) query.delete(key);
    try {
      const rows=await app.request(`/api/students?${query.toString()}`);
      document.getElementById('student-results').innerHTML=table(['Roll number','Name','Department','CGPA / 10','Backlogs'],rows.map(s=>[s.roll_no,s.name,s.department_name||'—',s.cgpa??'—',s.active_backlogs??'—']));
    } catch(error) { app.notice(error.message,'warning'); }
  });
  async function load() {
    try {
      const data = await app.request('/api/dashboard');
      if (data.summary) {
        cards([['Students',data.summary.students],['Faculty',data.summary.faculty],['Companies',data.summary.companies],['Open roles',data.summary.open_jobs],['Applications',data.summary.applications]]);
        document.getElementById('workspace-caption').textContent='Recently posted campus opportunities';
        document.getElementById('workspace').innerHTML=table(['Role','Company','Deadline'],(data.jobs||[]).map(x=>[x.title,x.company_name,x.application_deadline||'Open until filled']));
      } else if (data.student) {
        cards([['Roll number',data.student.roll_no],['CGPA / 10',data.academic?.cgpa ?? 'Not entered'],['Applications',data.applications.length],['Backlogs',data.academic?.active_backlogs ?? 'Not entered']]);
        document.getElementById('workspace').innerHTML=table(['Role','Company','Application status','Applied'],(data.applications||[]).map(x=>[x.title,x.company_name,x.status,new Date(x.applied_at).toLocaleDateString()]));
        document.querySelector('[data-own-skills]').dataset.endpoint=`/api/students/${data.student.student_id}/skills`;
        document.getElementById('open-jobs').hidden=false;
        const jobList=document.getElementById('job-list');
        if (!(data.jobs||[]).length) jobList.innerHTML='<div class="empty-note">No new opportunities are open right now.</div>';
        else jobList.innerHTML=`<table class="table"><thead><tr><th>Role</th><th>Company</th><th>Minimum CGPA</th><th>Deadline</th><th></th></tr></thead><tbody>${data.jobs.map(j=>`<tr><td>${esc(j.title)}</td><td>${esc(j.company_name)}</td><td>${esc(j.minimum_cgpa)}</td><td>${esc(j.application_deadline||'Open until filled')}</td><td><button class="btn btn-sm btn-primary" data-apply="${Number(j.job_id)}">Apply</button></td></tr>`).join('')}</tbody></table>`;
        jobList.querySelectorAll('[data-apply]').forEach(button=>button.addEventListener('click',async()=>{
          button.disabled=true;
          try { await app.request(`/api/jobs/${button.dataset.apply}/apply`,{method:'POST',body:'{}'}); app.notice('Application submitted.'); await load(); }
          catch(error) { app.notice(error.message,'warning'); button.disabled=false; }
        }));
      } else if (data.profile_missing) {
        cards([['Account','Student profile pending']]);
        document.getElementById('workspace').innerHTML='<div class="empty-note">An administrator needs to finish linking your student profile.</div>';
      } else {
        cards([['Courses',data.courses?.length||0],['Teaching','Academic workspace']]);
        document.getElementById('workspace').innerHTML=table(['Course','Name','Enrolled'],(data.courses||[]).map(x=>[x.course_code,x.course_name,x.enrolled]));
      }
      if (['admin','placement_officer'].includes(role)) await loadApplications();
      if (['admin','placement_officer'].includes(role)) await loadReport();
    } catch (error) { app.notice(error.message,'warning'); }
  }
  async function loadApplications() {
    const panel=document.getElementById('application-management');
    panel.hidden=false;
    try {
      const rows=await app.request('/api/applications');
      const target=document.getElementById('application-list');
      if (!rows.length) { target.innerHTML='<div class="empty-note">Applications will appear here as students apply.</div>'; return; }
      const statuses=['applied','shortlisted','rejected','withdrawn','offered','hired'];
      target.innerHTML=`<table class="table"><thead><tr><th>Student</th><th>Opening</th><th>Status</th><th>Review</th><th>Interview</th><th>Offer</th></tr></thead><tbody>${rows.map(a=>`<tr><td>${esc(a.student_name)}<div class="small text-secondary">${esc(a.roll_no)}</div></td><td>${esc(a.title)}<div class="small text-secondary">${esc(a.company_name)}</div></td><td>${esc(a.status)}</td><td><select class="form-select form-select-sm" data-status-for="${Number(a.application_id)}">${statuses.map(s=>`<option ${s===a.status?'selected':''}>${s}</option>`).join('')}</select><button class="btn btn-sm btn-outline-primary mt-1" data-save-status="${Number(a.application_id)}">Save</button></td><td><form class="mini-form" data-interview="${Number(a.application_id)}"><input class="form-control form-control-sm mb-1" name="round_number" type="number" min="1" placeholder="Round" required><input class="form-control form-control-sm mb-1" name="scheduled_at" type="datetime-local" required><button class="btn btn-sm btn-outline-secondary">Schedule</button></form></td><td><form class="mini-form" data-offer="${Number(a.application_id)}"><input class="form-control form-control-sm mb-1" name="package_amount" type="number" min="0.01" step="0.01" placeholder="Package" required><button class="btn btn-sm btn-outline-secondary">Record offer</button></form></td></tr>`).join('')}</tbody></table>`;
      target.querySelectorAll('[data-save-status]').forEach(button=>button.addEventListener('click',async()=>{
        const id=button.dataset.saveStatus, status=target.querySelector(`[data-status-for="${id}"]`).value;
        try { await app.request(`/api/applications/${id}`,{method:'PATCH',body:JSON.stringify({status})}); app.notice('Application status updated.'); await load(); }
        catch(error) { app.notice(error.message,'danger'); }
      }));
      target.querySelectorAll('[data-interview]').forEach(form=>form.addEventListener('submit',async event=>{
        event.preventDefault();const d=Object.fromEntries(new FormData(form).entries());d.mode='online';
        try { await app.request(`/api/applications/${form.dataset.interview}/interviews`,{method:'POST',body:JSON.stringify(d)});app.notice('Interview scheduled.');form.reset(); }
        catch(error) { app.notice(error.message,'danger'); }
      }));
      target.querySelectorAll('[data-offer]').forEach(form=>form.addEventListener('submit',async event=>{
        event.preventDefault();const d=Object.fromEntries(new FormData(form).entries());d.currency='INR';
        try { await app.request(`/api/applications/${form.dataset.offer}/offers`,{method:'POST',body:JSON.stringify(d)});app.notice('Offer recorded.');await load(); }
        catch(error) { app.notice(error.message,'danger'); }
      }));
    } catch(error) { app.notice(error.message,'warning'); }
  }
  async function loadReport() {
    try {
      const r=await app.request('/api/reports/overview');
      const ctx=document.getElementById('placementChart');
      document.getElementById('report-note').hidden=true;
      new Chart(ctx,{type:'bar',data:{labels:r.departments.map(x=>x.department_name),datasets:[{label:'Placed students',data:r.departments.map(x=>x.placed),backgroundColor:'#315fe8',borderRadius:5},{label:'Students',data:r.departments.map(x=>x.students),backgroundColor:'#dce5ff',borderRadius:5}]},options:{responsive:true,plugins:{legend:{position:'bottom'}},scales:{y:{beginAtZero:true,ticks:{precision:0}}}}});
    } catch (_) { document.getElementById('report-note').textContent='Reports will appear after the database has been initialized and placement records are available.'; }
  }
  document.getElementById('refresh').addEventListener('click',load);
  document.querySelectorAll('[data-api-form]').forEach(form=>form.addEventListener('submit',async event=>{
    event.preventDefault();
    const values=Object.fromEntries(new FormData(form).entries());
    if (form.hasAttribute('data-student-endpoint')) { const id=values.student_id; delete values.student_id; form.dataset.endpoint=`/api/students/${Number(id)}/${form.dataset.studentEndpoint}`; }
    if (form.hasAttribute('data-company-recruiter')) { const id=values.company_id; delete values.company_id; form.dataset.endpoint=`/api/companies/${Number(id)}/recruiters`; }
    if ('required_skills' in values) values.required_skills=values.required_skills.split(',').map(s=>s.trim()).filter(Boolean);
    if ('skills' in values) values.skills=values.skills.split(',').map(s=>s.trim()).filter(Boolean);
    for (const key of ['department_id','credits','company_id','student_id','course_id','semester_id','enrollment_id','round_number','minimum_cgpa','minimum_tenth_percentage','minimum_twelfth_percentage','maximum_active_backlogs','cgpa','tenth_percentage','twelfth_percentage','active_backlogs','score','maximum_score','minimum_cgpa']) if (values[key] !== undefined && values[key] !== '') values[key]=Number(values[key]);
    try { await app.request(form.dataset.endpoint,{method:form.dataset.method,body:JSON.stringify(values)}); app.notice('Saved successfully.'); form.reset(); await load(); }
    catch (error) { app.notice(error.message,'danger'); }
  }));
  load();
})();
