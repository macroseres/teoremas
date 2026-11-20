import re,html
SYM={'oint':'∮','iint':'∬','iiint':'∭','tilde':'~','notin':'∉','leftarrow':'←','rightarrow':'→','longrightarrow':'⟶','Longrightarrow':'⟹','iff':'⟺','implies':'⟹','cong':'≅','nmid':'∤','varnothing':'∅','ell':'ℓ','hbar':'ℏ','lfloor':'⌊','rfloor':'⌋','lceil':'⌈','rceil':'⌉','supseteq':'⊇','supset':'⊃','subsetneq':'⊊','ll':'≪','gg':'≫','propto':'∝','star':'⋆','bullet':'•','lim':'lim','Re':'ℜ','Im':'ℑ','aleph':'ℵ','bigcup':'⋃','bigcap':'⋂','sqcup':'⊔','vdots':'⋮','ddots':'⋱','top':'⊤','bot':'⊥','le':'≤','cdot':'·','times':'×','le':'≤','leq':'≤','ge':'≥','geq':'≥','ne':'≠','neq':'≠','in':'∈','angle':'∠','circ':'∘','ldots':'…','cdots':'⋯','to':'→','infty':'∞','pm':'±','sum':'∑','prod':'∏','mid':'∣','approx':'≈','equiv':'≡','cap':'∩','cup':'∪','subseteq':'⊆','subset':'⊂','forall':'∀','exists':'∃','Rightarrow':'⇒','Leftrightarrow':'⇔','mapsto':'↦','perp':'⟂','parallel':'∥','nabla':'∇','partial':'∂','int':'∫','setminus':'∖','emptyset':'∅','neg':'¬','land':'∧','lor':'∨','oplus':'⊕','otimes':'⊗','langle':'⟨','rangle':'⟩','sim':'∼','mid':'∣','dots':'…','vee':'∨','wedge':'∧','triangle':'△','mp':'∓'}
GREEK={n:c for n,c in zip('alpha beta gamma delta epsilon varepsilon theta lambda mu nu pi rho sigma tau phi varphi chi psi omega Gamma Delta Theta Lambda Pi Sigma Phi Psi Omega eta zeta kappa xi iota'.split(),'αβγδϵεθλμνπρστϕφχψωΓΔΘΛΠΣΦΨΩηζκξι')}
FUN='limsup liminf sgn arcsin arccos arctan sinh cosh tanh Pr sin cos tan cot sec csc log ln exp lim max min gcd mdc sup inf det dim ker deg arg Var Cov mod'.split()
OPS=set('+-=<>/!*')
def esc(s): return html.escape(s,quote=False)
class P:
    def __init__(s,t): s.t=t;s.i=0
    def peek(s): return s.t[s.i] if s.i<len(s.t) else ''
    def group(s):
        while s.peek()==' ': s.i+=1
        if s.peek()=='{':
            s.i+=1; d=1; j=s.i
            while d:
                c=s.t[s.i]; d+= (c=='{')-(c=='}'); s.i+=1
            return s.t[j:s.i-1]
        if s.peek()=='\\':
            m=re.match(r'\\([A-Za-z]+|.)',s.t[s.i:]); s.i+=m.end(); return m.group(0)
        c=s.peek(); s.i+=1; return c
    def atom(s):
        c=s.peek()
        if c==' ': s.i+=1; return ''
        if c=='{': return '<mrow>'+tomml(s.group())+'</mrow>'
        if c=='\\':
            m=re.match(r'\\([A-Za-z]+|.)',s.t[s.i:]); name=m.group(1); s.i+=m.end()
            if name in('frac','tfrac','dfrac'): a=s.group(); b=s.group(); return f'<mfrac><mrow>{tomml(a)}</mrow><mrow>{tomml(b)}</mrow></mfrac>'
            if name=='sqrt':
                if s.peek()=='[':
                    j=s.t.index(']',s.i); n=s.t[s.i+1:j]; s.i=j+1; a=s.group(); return f'<mroot><mrow>{tomml(a)}</mrow><mrow>{tomml(n)}</mrow></mroot>'
                a=s.group(); return f'<msqrt>{tomml(a)}</msqrt>'
            if name=='overrightarrow': a=s.group(); return f'<mover accent="true"><mrow>{tomml(a)}</mrow><mo stretchy="true">→</mo></mover>'
            if name in('overline','bar'): a=s.group(); return f'<mover accent="true"><mrow>{tomml(a)}</mrow><mo stretchy="true">‾</mo></mover>'
            if name=='hat': a=s.group(); return f'<mover accent="true"><mrow>{tomml(a)}</mrow><mo>^</mo></mover>'
            if name in('text','mathrm','operatorname'): a=s.group(); return f'<mtext>{esc(a)}</mtext>' if name=='text' else f'<mi mathvariant="normal">{esc(a)}</mi>'
            if name in('mathbb','mathbf','mathcal'):
                a=s.group(); v={'mathbb':'double-struck','mathbf':'bold','mathcal':'script'}[name]
                return f'<mi mathvariant="{v}">{esc(a)}</mi>'
            if name=='begin':
                env=s.group(); end='\\end{'+env+'}'
                j=s.t.index(end,s.i); body=s.t[s.i:j]; s.i=j+len(end)
                rows=[r for r in body.split('\\\\') if r.strip()]
                tab='<mtable>'+''.join('<mtr>'+''.join(f'<mtd>{tomml(c)}</mtd>' for c in r.split('&'))+'</mtr>' for r in rows)+'</mtable>'
                L,R={'pmatrix':('(',')'),'bmatrix':('[',']'),'vmatrix':('|','|'),'matrix':('','')}.get(env,('',''))
                lo=f'<mo fence="true">{L}</mo>' if L else ''; ro=f'<mo fence="true">{R}</mo>' if R else ''
                return lo+tab+ro
            if name in ('%','&','#','$','_'):
                return f'<mo>{name}</mo>'
            if name=='pmod':
                a=s.group(); return f'<mspace width="1em"/><mo stretchy="false">(</mo><mi>mod</mi><mspace width="0.3em"/>{tomml(a)}<mo stretchy="false">)</mo>'
            if name=='bmod':
                return '<mspace width="0.3em"/><mo>mod</mo><mspace width="0.3em"/>'
            if name=='binom':
                a=s.group(); b=s.group(); return f'<mo stretchy="false">(</mo><mfrac linethickness="0"><mrow>{tomml(a)}</mrow><mrow>{tomml(b)}</mrow></mfrac><mo stretchy="false">)</mo>'
            if name=='not':
                return '<mo≯</mo>'
            if name in('big','Big','bigg','Bigg'):
                d=s.group(); return f'<mo stretchy="false">{esc(d)}</mo>'
            if name in('quad','qquad'): return '<mspace width="1em"/>'
            if name in(',',';',' ',':','!'): return '<mspace width="0.2em"/>'
            if name=='|': return '<mo fence="false" stretchy="false">‖</mo>'
            if name=='{': return '<mo stretchy="false">{</mo>'
            if name=='}': return '<mo stretchy="false">}</mo>'
            if name in('left','right'):
                d=s.group(); d={'.':''}.get(d,d); d={'\\{':'{','\\}':'}','\\|':'‖','\\langle':'⟨','\\rangle':'⟩'}.get(d,d)
                return f'<mo fence="true">{esc(d)}</mo>' if d else ''
            if name in GREEK: return f'<mi>{GREEK[name]}</mi>'
            if name in FUN: return f'<mi>{name}</mi>'
            if name in SYM:
                ch=SYM[name]
                if name in('sum','prod','int'): return f'<mo>{ch}</mo>'
                return f'<mo>{ch}</mo>'
            raise ValueError('cmd '+name)
        if c.isdigit() or (c=='.' and s.t[s.i+1:s.i+2].isdigit()):
            m=re.match(r'\d*\.?\d+|\d+',s.t[s.i:]); s.i+=m.end(); return f'<mn>{m.group(0)}</mn>'
        s.i+=1
        if c.isalpha(): return f'<mi>{c}</mi>'
        if c in '()[]': return f'<mo stretchy="false">{c}</mo>'
        if c=='|': return '<mo fence="false" stretchy="false">∣</mo>'
        if c=="'": return '<mo>′</mo>'
        if c=='-': return '<mo>−</mo>'
        if c==',': return '<mo separator="true">,</mo>'
        if c=='&': return ''
        return f'<mo>{esc(c)}</mo>'
def tomml(t):
    p=P(t); out=[]
    while p.i<len(t):
        a=p.atom()
        if a=='' : continue
        sub=sup=None
        while p.peek() in('^','_',' '):
            if p.peek()==' ': p.i+=1; continue
            k=p.peek(); p.i+=1
            g=p.group()
            x= '<mrow>'+tomml(g)+'</mrow>' if (len(g)>1 or g.startswith('\\')) else tomml(g)
            if k=='^': sup=x
            else: sub=x
        if sub and sup: a=f'<msubsup>{a}{sub}{sup}</msubsup>'
        elif sup: a=f'<msup>{a}{sup}</msup>'
        elif sub: a=f'<msub>{a}{sub}</msub>'
        out.append(a)
    return ''.join(out)
NS='xmlns="http://www.w3.org/1998/Math/MathML"'
def span(tex,display=False):
    m=tomml(tex)
    d=' display="block"' if display else ''
    return f'<span class="katex"><math{d} {NS}><semantics><mrow>{m}</mrow><annotation encoding="application/x-tex">{esc(tex)}</annotation></semantics></math></span>'
def render(snip):
    snip=re.sub(r'\$\$(.+?)\$\$',lambda m:'</p><div class="formula-line">'+span(m.group(1).strip(),True)+'</div><p>',snip,flags=re.S)
    r=re.sub(r'\$(.+?)\$',lambda m:span(m.group(1)),snip,flags=re.S)
    return r.replace('<p></p>','')
