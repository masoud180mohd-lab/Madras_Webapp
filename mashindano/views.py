from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Mshiriki, Alama, Kitengo
from usimamizi.models import Mwalimu

@login_required(login_url='ingia')
def dashbodi_jaji(request):
    try:
        jaji_wetu = Mwalimu.objects.get(user=request.user)
    except Mwalimu.DoesNotExist:
        messages.error(request, "Akaunti yako haina hadhi ya Ujaji.")
        return redirect('mwanzo')

    washiriki = Mshiriki.objects.all().order_by('kitengo', 'namba_ya_kifua')
    return render(request, 'mashindano/dashbodi_jaji.html', {'washiriki': washiriki, 'jaji': jaji_wetu})

@login_required(login_url='ingia')
def weka_alama(request, mshiriki_id):
    mshiriki = get_object_or_404(Mshiriki, id=mshiriki_id)
    jaji_wetu = get_object_or_404(Mwalimu, user=request.user)
    alama_zilizopo = Alama.objects.filter(mshiriki=mshiriki, jaji=jaji_wetu).first()

    if request.method == 'POST':
        # Tunachukua idadi ya makosa kutoka kwenye form
        data = {
            'saka_kubwa': int(request.POST.get('saka_kubwa', 0)),
            'saka_dogo': int(request.POST.get('saka_dogo', 0)),
            'kibw': int(request.POST.get('kibw', 0)),
            'neno': int(request.POST.get('neno', 0)),
            'shakli': int(request.POST.get('shakli', 0)),
            'makosa_tajweed': int(request.POST.get('makosa_tajweed', 0)),
            'makosa_makharij': int(request.POST.get('makosa_makharij', 0)),
        }

        if alama_zilizopo:
            for key, value in data.items():
                setattr(alama_zilizopo, key, value)
            alama_zilizopo.save()
        else:
            Alama.objects.create(mshiriki=mshiriki, jaji=jaji_wetu, **data)
            
        messages.success(request, f'✅ Alama za Mshiriki {mshiriki.namba_ya_kifua} zimehifadhiwa!')
        return redirect('dashbodi_jaji')

    return render(request, 'mashindano/fomu_alama.html', {
        'mshiriki': mshiriki, 
        'alama': alama_zilizopo
    })