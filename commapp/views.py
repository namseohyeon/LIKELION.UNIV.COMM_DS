from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from .models import comm, Comment,  ReComment, Commit
from django.views.generic import View, CreateView
from commapp.forms import CommentForm, commForm, ReCommentForm
import requests
from account.models import CustomUser
import base64
from urllib import parse
import re
# Create your views here.

def main(request):
    return render(request, 'main.html')

def test(request):
    return render(request, 'test.html')

def about(request):
    return render(request, 'about.html')

def board_post(request):
    if request.method == 'POST' or request.method=='FILES': #POST요청 폼의 버튼을 눌렀다
        form  = commForm(request.POST, request.FILES) #form 유효성 확인
        if form.is_valid():
            c = form.save(commit=False) #db에 당장 저장x
            c.user = request.user
            c.save()
            return redirect('board_detail', pk = c.pk)
    else: #GET요청 웹 브라우저에서 페이지 접속
        form = commForm()
    return render(request, 'board_post.html', {'form':form})

def board(request):
    c = comm.objects.all().order_by('-id')
    return render(request, 'board.html',{'comm':c})

def board_detail(request, pk):
    # all = comm.objects.all()
    c = get_object_or_404(comm, pk=pk)
    form = CommentForm()
    reform = ReCommentForm()
    return render(request, 'board_detail.html',{'comm':c, 'comment_form':form,'recomment_form':reform})

def board_update(request, pk):
    c = get_object_or_404(comm,pk=pk)
    if(request.method == "POST" or request.method == 'FILES'):
        form = commForm(request.POST, request.FILES, instance=c)
        if(form.is_valid()):
            c = form.save(commit=False)
            c.save()
        return redirect('board_detail', pk=c.pk)
    else:
        form = commForm(instance=c)
        return render(request, 'board_post.html', {'form':form})

def board_delete(request,pk):
    c = get_object_or_404(comm,pk=pk)
    c.delete()
    return redirect('board')

def comment_create(request, pk):
    filled_form = CommentForm(request.POST)
    if filled_form.is_valid():
        finished_form = filled_form.save(commit=False)
        finished_form.post = get_object_or_404(comm, pk=pk)
        finished_form.user = request.user
        finished_form.save()
    return redirect('board_detail', pk)

def comment_update(request, pk):
    c = get_object_or_404(Comment,pk=pk) # 모델로부터 객체를 받을 때 객체가 있으면 받고, 없을 시 404 에러 페이지를 보여줌
    p = get_object_or_404(comm,pk=c.post.pk)
    if(request.method == "POST"):
        form = CommentForm(request.POST, instance=c)
        if(form.is_valid()):
            c = form.save(commit=False)
            c.save()
        return redirect('board_detail', pk=p.pk) #댓글 모델의 포스트pk값을 받아서 디테일페이지/pk로 사요
    else:
        form = CommentForm(instance=c) #CommentForm에 정보 넣음
        return render(request, 'board_post.html', {'form':form}) #render함수를 통해 board_post에 form을 넣는다.
def comment_delete(request, pk):
    c = get_object_or_404(Comment,pk=pk)
    p = get_object_or_404(comm, pk=c.post.pk)
    c.delete()
    return redirect('board_detail', pk=p.pk)

def recomment_create(request,c_pk):
    filled_form = ReCommentForm(request.POST)
    if filled_form.is_valid():
        finished_form = filled_form.save(commit=False)
        finished_form.post = get_object_or_404(Comment, pk=c_pk)
        finished_form.user = request.user
        finished_form.save()
    return redirect('board_detail', pk=finished_form.post.post.pk)

def recomment_delete(request, rc_pk):
    # c = get_object_or_404(Comment, pk=pk)
    rc = get_object_or_404(ReComment, pk=rc_pk)
    p = get_object_or_404(comm, pk=rc.post.post.pk)
    rc.delete()
    return redirect('board_detail', pk=p.pk)

def search(request):
    post=comm.objects.all().order_by('-id')

    q = request.POST.get('search','')
    if q:
        post=post.filter(title__icontains=q)
        return render(request, 'search.html',{'post':post, 'q':q})
    else:
        return render(request, 'search.html',{'post':post})

class GithubUserView(View):
    def get(self, request, username):
        # username,repos = requset.GET['username','repos']
        # repos = requset.GET['repos']
        url1 = 'https://api.github.com/users/%s/repos?per_page=100' %(username)
        response1 = requests.get(url1).json()
        arr = []
        count=0
        for i in range(len(response1)-1, 0,-1):
            push=response1[i]["pushed_at"]
            push1 = push[0:10]
            push2 = push1.split('-')
            push3 = ''.join(push2)
            if(20220803 <= int(push3)):
                arr.append(response1[i]["name"])
       
        for i in arr:
            url = 'https://api.github.com/repos/%s/%s/commits?per_page=100' %(username, i)
            response = requests.get(url).json()
            for j in range(len(response)):
                time=response[j]["commit"]["author"]["date"]
                string1 = time[0:10]
                string1 = string1.split('-')
                string = ''.join(string1)
                if int(string) >= 20220803 :
                    count += 1
                else:
                    break
        commit=Commit.objects.all()
        if commit.filter(gitName__icontains=username).exists():
            # commit.author['username'].update(
            #     commit = count
            # )
            commit.filter(gitName=username).update(commit = count)
        else:
            commit.gitName = username
            commit.commit = count
        return render(request, 'commit.html',{'name':arr, 'repos':count})
        # return render(requset, 'commit.html',{'name':username, 'repos':arr})

def commit_rank(request):
    commit = Commit.objects.all().order_by('-commit')
    return render(request, 'commit_rank.html',{'commit':commit})

def mypage(request):
    # n=request.user
    # m=str(request.user)
    n=CustomUser.objects.get(username=request.user.username)
    name1=n.git
    # name1 = n.git
    # x = "namseohyeon"
    # repo = "DAASHeo
    # x = "namseohyeon"
    # name = "DAASHeo"
    # repo = "DAASHeo"
    commit=Commit.objects.all()
    # # # commit.gitName=request.POST['gitName']
    url = 'https://api.github.com/repos/%s/%s/readme' %(name1,name1)
    response = requests.get(url).json()
    readme=response.get('content')
    if readme:
    # # read=readme.decode("UTF-8")
        r=base64.b64decode(readme)
        read=r.decode("UTF-8")
        x=read.replace('<div align="center">','').replace('</div>','').replace('<h1>','#').replace('<h2>','##').replace('<h3>','###').replace('<h4>','####').replace('<h5>','#####').replace('<h6>','######').replace('<p>','').replace('</h1>','').replace('</h2>','').replace('</h3>','').replace('</h4>','').replace('</h5>','').replace('</h6>','').replace('</p>','').replace('<br>','').replace('<br/>','').replace('<strong>','**').replace('</strong>','**').replace('<img src="','![image](').replace('/>',')').replace('<a href="','[''](').replace('">',')').replace('</a>','')
    else:
        x = "git readme가 없습니다"
    # p_url = 'https://api.github.com/users/%s' %(name1)
    # p_response = requests.get(p_url).json()
    #.replace('<a href="','(').replace('">',')')
    #.replace('<img src="','![image](').replace('/>',')').replace('<img src="','![image](')
    #.replace('<a href="','[](').replace('>',')')
    #.replace('>',')').replace('<a href="','[](')
    # .replace('">',')').replace('<img src="','![image](').replace('/>',')')
    # q=[m.start() for m in re.finditer('<', x)]
    # for i in range(len(q)):
    # while True:
    # #     if x.find("<") != -1:
    # i3=x3.find("<a>")
    # x4=x3[:i3]
    # i4=x3.find("</a>")
    # x5=x[i4:]
    # x6=x4+x5
        # else:
        #     break
    #readme=parse.urlencode(response, encoding='UTF-8', doseq=True)
                # .then((response) => response.json())
                # .then((data) =>{
                #     console.log(data) // json 파일
                #     console.log(data.content) //파일 내용 base64로 받아와진다
                #     document.write(decodeURIComponent(atob(data.content))); //utf-8로 디코딩
                # });
    # return render(request, 'mypage.html',{'commit':commit,'readme':x,'img':p_response['avatar_url']})
    return render(request, 'mypage.html',{'commit':commit,'readme':x,})
    #return render(request, 'mypage.html',{'commit':commit,'readme':x})



def Co(request):
    # username,repos = requset.GET['username','repos']
    # repos = requset.GET['repos']
    username=request.POST['gitName']  
    # CustomUser.git =request.POST['gitName'] 
    url1 = 'https://api.github.com/users/%s/repos?per_page=100' %(username)
    
    response1 = requests.get(url1).json()
    arr = []
    count=0
    for i in range(len(response1)-1, 0,-1):
        push=response1[i]["pushed_at"]
        push1 = push[0:10]
        push2 = push1.split('-')
        push3 = ''.join(push2)
        if(20220815 <= int(push3)):
            arr.append(response1[i]["name"])
    
    for i in arr:
        url = 'https://api.github.com/repos/%s/%s/commits?per_page=100' %(username, i)
        response = requests.get(url).json()
        for j in range(len(response)):
            time=response[j]["commit"]["author"]["date"]
            string1 = time[0:10]
            string1 = string1.split('-')
            string = ''.join(string1)
            if int(string) >= 20220815 :
                count += 1
            else:
                break
    commit=Commit.objects.all()
    if commit.filter(gitName__icontains=username).exists():
        commit.filter(gitName=username).update(commit = count)
    else:
        Commit.objects.create(
            user = request.user,
            gitName = username,
            commit = count
        )
    CustomUser.objects.filter(username=request.user).update(git=username)
    #     commit.author['username'].update(
    #         commit = count
    #     )
    #     commit.filter(gitName=username).update(commit = count)
    #     commit.save()
    # else:
    #     c = Commit.objects.create(gitName = username, commit = count)
    #     c.save()
    return render(request, 'commit.html',{'name':arr, 'repos':count})
    # return render(request, 'commit.html',{'commit':c})