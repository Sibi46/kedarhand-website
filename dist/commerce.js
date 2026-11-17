// Progressive enhancements for the Django storefront.
let storeConfig = null;
const baseContact = contact, baseArt = art, commerceRender = render;
art = function(p) {
  return p.image ? `<a class="product-art" href="/products/${encodeURIComponent(p.id)}/"><img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" loading="lazy" style="width:100%;height:100%;min-height:240px;max-height:460px;object-fit:contain"></a>` : baseArt(p);
};
contact = function() {
  const links = storeConfig ? [['WhatsApp',storeConfig.whatsapp?'https://wa.me/'+storeConfig.whatsapp:''],['Instagram',storeConfig.instagram],['Facebook',storeConfig.facebook]].filter(([,url])=>url).map(([name,url])=>`<a class="btn light" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${name} ↗</a>`).join(' ') : '';
  return baseContact().replace(/<p id="contact-social">[\s\S]*?<\/p>/, storeConfig ? `<p id="contact-social">${links}</p>` : '$&').replace('</section>', `<h2>Send an enquiry</h2><form id="contact-enquiry"><div class="form-grid"><label>Your name<input name="name" required maxlength="100" autocomplete="name"></label><label>Email<input name="email" type="email" required maxlength="254" autocomplete="email"></label></div><label>How can we help?<textarea name="message" rows="5" required maxlength="3000"></textarea></label><p><button class="btn">Send enquiry</button></p><p id="form-error" role="status"></p></form></section>`);
};
render = function() {
  commerceRender();
  const route = location.hash.slice(1) || 'home';
  if (['shop','all-products','coffee','tea','edible-oils'].includes(route)) {
    const scoped = products.filter(p=>['shop','all-products'].includes(route)||p.cat===route);
    const subcategories = [...new Set(scoped.map(p=>p.subcategory).filter(Boolean))].sort();
    if(subcategories.length) {
      const filter=document.createElement('label');
      filter.style.cssText='display:block;max-width:320px;margin:20px 0';
      filter.innerHTML=`Subcategory<select id="subcategory-filter"><option value="">All subcategories</option>${subcategories.map(s=>`<option value="${escapeHTML(s)}">${escapeHTML(s)}</option>`).join('')}</select>`;
      const heading=app.querySelector('h1');
      if(heading)heading.after(filter);
    }
  }
  if (storeConfig && route==='checkout') {
    const note=document.createElement('p');
    note.textContent=`Standard shipping: ${money(storeConfig.shipping_fee)}.${storeConfig.free_shipping_above!==null?' Free shipping on discounted subtotals from '+money(storeConfig.free_shipping_above)+'.':''} ${storeConfig.shipping_note}`;
    const form=app.querySelector('#checkout');
    if(form)form.before(note);
  }
  // Expose real URLs for crawlers and shared product links.
  app.querySelectorAll('a[href^="#product/"]').forEach(a=>{a.href='/products/'+encodeURIComponent(a.getAttribute('href').slice(9))+'/'});
  const p=route.startsWith('product/')?products.find(p=>p.id===route.split('/')[1]):null;
  if(p)document.title=p.name+' | Kedarmart';
};
document.addEventListener('change',e=>{
  if(e.target.id!=='subcategory-filter')return;
  const value=e.target.value;
  app.querySelectorAll('article').forEach(article=>{
    const button=article.querySelector('[data-add]');
    const p=products.find(p=>p.id===button?.dataset.add);
    article.hidden=!!value&&p?.subcategory!==value;
  });
});
document.addEventListener('submit',async e=>{
  if(e.target.id!=='contact-enquiry')return;
  e.preventDefault();
  const form=e.target, button=form.querySelector('button'), status=form.querySelector('#form-error');
  button.disabled=true;
  try {
    if(!backendReady)throw new Error('Connecting to the store. Please try again.');
    const result=await api('contact','POST',Object.fromEntries(new FormData(form)));
    form.reset();status.textContent=result.message;
  } catch(error){status.textContent=error.message}
  finally{button.disabled=false}
},true);
api('configuration').then(config=>{storeConfig=config;if(backendReady)render()}).catch(()=>{});
