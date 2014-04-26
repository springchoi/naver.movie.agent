# -*- coding: utf-8 -*-

import re
import datetime
import urllib2

NAVER_SEARCH_URL = "http://movie.naver.com/movie/search/result.nhn"
NAVER_CONTENT_URL = "http://movie.naver.com/movie/bi/mi/basic.nhn"

def Start():
	HTTP.CacheTime = CACHE_1MINUTE

class NaverMovieAgent(Agent.Movies):
	name = "Naver Movie"
	languages = [Locale.Language.Korean]

	primary_provider = True
	#fallback_agent = False
	accepts_from = ['com.plexapp.agents.localmedia']
	#contributes_to = None

	def search(self, results, media, lang, manual):
		Log("%s (%s)" % (media.name, media.year))

		url = "http://movie.naver.com/movie/search/result.nhn?section=movie&ie=utf8&query=%s" % urllib2.quote(media.name)
		try:
			html = HTML.ElementFromURL(url, encoding='euc-kr')
		except Exception, e:
			Log(e)
			return

		content = html.xpath('//div[@id="old_content"]')[0]

		for entry in html.xpath('//ul[@class="search_list_1"]/li'):
			node = entry.xpath('.//dt/a')[0]
			title = node.text_content()
			url = node.get('href')
			cotentId = re.search('code=(\d+)', url).group(0).strip('code=')
			etc = entry.xpath('.//dd[@class="etc"]')[0].text_content().rpartition('|')
			year = int(etc[-1].strip())
			if media.year:
				if abs(int(media.year) - year) > 2:
					Log("Skip this %s coz year" % title)
					continue
			elif media.year:
				year = media.year

			uid = "%s_%s" % (cotentId, year)
			#score = int(float(entry.xpath('userRating')[0].text) * 10)
			# TODO : use string matching score
			score = 85
			Log("%s %s %s %s" % (year, title, score, uid))
			results.Append(MetadataSearchResult(id=uid, name=title, year=year, score=score, lang=lang))

	def update(self, metadata, media, lang, force):
		(uid, year) = metadata.id.split('_')
		url = "%s?code=%s" % (NAVER_CONTENT_URL, metadata.id)
		Log(url)

		html = HTML.ElementFromURL(NAVER_CONTENT_URL, {'code':uid}, encoding='utf-8')

		metadata.title = html.xpath("//h3[@class='h_movie']/a")[0].text
		Log("Title : %s (%s)" % (metadata.title, metadata.id))
		html = html.xpath("//*[@id='content']")[0]

		orgTitle = html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/strong")
		if orgTitle:
			metadata.original_title = orgTitle[0].text.rpartition(',')[0].strip()

		try:
			metadata.rating = round(float(html.xpath(".//div[@class='sc_view']/div[@class='star_score']//em")[0].text), 2)
			Log("Rate : '%s'" % html.xpath(".//div[@class='sc_view']/div[@class='star_score']//em")[0].text)
		except Exception, e:
			Log(html.xpath(".//div[@class='sc_view']/div[@class='star_score']//em"))

		metadata.genres.clear()
		for genre in html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[1]/a"):
			Log(genre.text)
			metadata.genres.add(genre.text.strip())

		metadata.countries.clear()
		for node in html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[2]/a"):
			metadata.countries.add(node.text)
			#Log("Country : %s" % node[0].text)

		metadata.duration = 0
		node = html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[3]")
		if node and node[0].text:
			query = re.match("(\d+)분", node[0].text)
			if query:
				metadata.duration = int(query.group(1))*60*1000
				#Log("Dur : %s" % metadata.duration)


		#year = (metadata.original_title.rpartition(',')[-1]).strip()
		#html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[4]/a[1]")[0].text
		
		if year:
			metadata.year = int(year)

		if metadata.duration > 0:
			nodes = html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[4]/a")
		else:
			nodes = html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[1]/p/span[3]/a")

		if nodes:
			metadata.originally_available_at = datetime.datetime.strptime(nodes[0].text+nodes[1].text, '%Y.%m.%d').date()
		
		metadata.directors.clear()
		
		for node in html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[2]/p/a"):
			metadata.directors.add(node.text)

		metadata.writers.clear()

		metadata.roles.clear()
		for node in html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[3]/p/a"):
			role = metadata.roles.new()
			role.actor = node.text


		node = html.xpath("./div[@class='article']/div[@class='mv_info_area']/div[@class='mv_info']/dl[@class='info_spec']/dd[4]/p/a")
		if node:
			age = node[0].text
			query = re.match("(\d+)세", age.encode('utf-8'))
			if query:
				metadata.content_rating_age = int(query.group(1))
		
		node = html.xpath(".//div[@class='story_area']//p")
		if node:
			summary = ""
			for text in node[0].itertext():
				summary += text.strip()
			metadata.summary = summary
		else:
			Log("NO - summary")

		try:
			urlPoster = html.xpath(".//div[@class='poster']/a/img")[0].get('src')
			orgPoster = urlPoster.split('?')[0]
			metadata.posters[orgPoster] = Proxy.Preview(urlPoster, sort_order = 1)
		except Exception, e:
			Log("Cannot find Poster")

