// Progressive enhancements for the Django storefront.
let storeConfig = null;
const baseContact = contact, baseArt = art, commerceRender = render;
art = function(p) {
  const photoBase = (window.KEDARMART_BASE_PATH || '') + '/static/assets/';
  const servingPhotos = {'instant-coffee': 'coffee-moment.jpg', 'blend-coffee': 'coffee-beans.jpg', 'cappuccino': 'coffee-table.jpg'};
  if (!p.image && servingPhotos[p.id]) return `<div class="product-art photo-product"><a href="${window.KEDARMART_BASE_PATH||''}/products/${encodeURIComponent(p.id)}/" aria-label="View ${escapeHTML(p.name)}"><img src="${photoBase + servingPhotos[p.id]}" alt="Coffee serving inspiration" loading="lazy"></a><span class="photo-disclaimer">Serving inspiration</span><button class="wish" data-wish="${escapeHTML(p.id)}" aria-label="Save ${escapeHTML(p.name)}" aria-pressed="${wishlist.includes(p.id)}">${wishlist.includes(p.id)?'&#9829;':'&#9825;'}</button></div>`;
  return p.image ? `<a class="product-art" href="${window.KEDARMART_BASE_PATH||''}/products/${encodeURIComponent(p.id)}/"><img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" loading="lazy" style="width:100%;height:100%;min-height:240px;max-height:460px;object-fit:contain"></a>` : baseArt(p);
};
contact = function() {
  const links = storeConfig ? [['WhatsApp',storeConfig.whatsapp?'https://wa.me/'+storeConfig.whatsapp:''],['Instagram',storeConfig.instagram],['Facebook',storeConfig.facebook]].filter(([,url])=>url).map(([name,url])=>`<a class="btn light" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${name} ↗</a>`).join(' ') : '';
  return baseContact().replace(/<p id="contact-social">[\s\S]*?<\/p>/, storeConfig ? `<p id="contact-social">${links}</p>` : '$&').replace('</section>', `<h2>Send an enquiry</h2><form id="contact-enquiry"><div class="form-grid"><label>Your name<input name="name" required maxlength="100" autocomplete="name"></label><label>Email<input name="email" type="email" required maxlength="254" autocomplete="email"></label></div><label>How can we help?<textarea name="message" rows="5" required maxlength="3000"></textarea></label><p><button class="btn">Send enquiry</button></p><p id="form-error" role="status"></p></form></section>`);
};
render = function() {
  commerceRender();
  const route = location.hash.slice(1) || 'home';
  if (['shop','all-products','coffee','tea','edible-oils'].includes(route)) {
    if (['coffee','edible-oils'].includes(route)) {
      const oil = route === 'edible-oils';
      const assets = (window.KEDARMART_BASE_PATH || '') + '/static/assets/';
      const category = storeCategories.find(item => item.slug === route);
      const photo = category?.image || assets + (oil ? 'oil-kitchen.jpg' : 'coffee-table.jpg');
      const section = app.querySelector('section');
      section.classList.add('photo-collection-page', oil ? 'oil-collection' : 'coffee-collection');
      section.insertAdjacentHTML('afterbegin', `<div class="collection-photo-hero"><div class="collection-photo-copy"><span class="editorial-tag">${oil ? 'THE KITCHEN COLLECTION' : 'THE COFFEE COLLECTION'}</span><h2>${oil ? 'Good food starts<br>with good essentials.' : 'Find your<br>coffee moment.'}</h2><p>${oil ? 'Explore our cold-pressed mustard oil for everyday cooking. Speak to our team about bottle sizes, availability and product details.' : 'From a quick morning cup to an unhurried coffee break. Explore instant coffee, our Arabica + Robusta blend and cappuccino premix.'}</p><button class="btn" type="button" data-scroll-collection>Explore ${oil ? 'edible oils' : 'coffee'} &#8595;</button><div class="collection-tags">${(oil ? ['Cold-pressed mustard oil','Everyday cooking'] : ['Instant coffee','Arabica + Robusta','Cappuccino']).map(text=>`<span>${text}</span>`).join('')}</div></div><figure><img src="${escapeHTML(photo)}" alt="${oil ? 'Cooking oil in a kitchen setting' : 'Coffee shared over a table'}" fetchpriority="high"><figcaption>${category?.image ? 'Our collection' : 'Lifestyle inspiration'}</figcaption></figure></div>`);
      section.insertAdjacentHTML('beforeend', `<div class="collection-photo-story"><img src="${assets + (oil ? 'kitchen-essentials.jpg' : 'coffee-beans.jpg')}" alt="${oil ? 'Kitchen ingredients and cooking oil' : 'Roasted coffee beans and ground coffee'}" loading="lazy"><div><span class="editorial-tag">${oil ? 'AT THE HEART OF YOUR KITCHEN' : 'FROM THE FIRST AROMA'}</span><h2>${oil ? 'For meals worth sharing.' : 'Make a little time<br>for a good cup.'}</h2><p>${oil ? 'Find an everyday essential for your kitchen. Our team can help with product information, pack sizes and availability.' : 'Explore the collection and choose the coffee that fits your day. Product details and available options are shown with each item.'}</p><a class="modern-link" href="#contact">Ask our team &#8599;</a></div></div>`);
    }
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
  app.querySelectorAll('a[href^="#product/"]').forEach(a=>{a.href=(window.KEDARMART_BASE_PATH||'')+'/products/'+encodeURIComponent(a.getAttribute('href').slice(9))+'/'});
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
function updateFooterSocial(config) {
  const target = document.querySelector('#footer-social');
  if (!target) return;
  target.querySelectorAll('[data-config-social]').forEach(link => link.remove());
  const links = [
    ['Facebook', config.facebook, '<span class="footer-social-letter" aria-hidden="true">f</span>'],
    ['Instagram', config.instagram, '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".7"/></svg>'],
    ['WhatsApp', /^\d{8,15}$/.test(config.whatsapp || '') ? 'https://wa.me/' + config.whatsapp : '', '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l-1 4 5-2a9 9 0 1 0-4-2z"/><path d="m8 7 2 3-1 1 4 4 1-1 3 2"/></svg>']
  ];
  links.filter(([,url])=>url && /^https:\/\//.test(url)).forEach(([name,url,icon]) => {
    target.insertAdjacentHTML('beforeend', `<a data-config-social href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer" aria-label="Kedarmart on ${name}">${icon}</a>`);
  });
}
api('configuration').then(config=>{storeConfig=config;updateFooterSocial(config);if(backendReady)render()}).catch(()=>{});
