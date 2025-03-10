<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:ditaarch="http://dita.oasis-open.org/architecture/2005/"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:atict="http://www.arbortext.com/namespace/atict"
    exclude-result-prefixes="xsi xs" version="2.0">
    <xsl:output method="xml" indent="yes"/>
   <!-- Add machinerytask doctype to all task topics -->
    <xsl:template match="/">
        <!--Remove white space and strange characters -->
        <xsl:variable name="fn0" select="tokenize(base-uri(.), '/')[last()]"/>
        <xsl:variable name="fn1" select="replace( $fn0, '%27' , '_' )"/>
        <xsl:variable name="fn11" select="replace( $fn1, '%20', '_')"/>
        
        <xsl:variable name="fn111" select="
            replace(
            replace(
            replace($fn11, ' ', '_'),
            '\+', '_'),
            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
        
        <xsl:variable name="filename" select="replace( $fn111 , 'SINGLEQUOTE' , '' )"/>
        <xsl:choose>
            <xsl:when test="/task">
                <xsl:result-document href="{$filename}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Machinery Task//EN" "machineryTask.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/bookmap">
                <xsl:variable name="bm" select="substring-before($filename , '.xml')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.ditamap' )"/>
                <xsl:result-document href="{$bookmap}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/map">
                <xsl:variable name="bm" select="substring-before($filename , '.xml')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.ditamap' )"/>
                <xsl:result-document href="{$bookmap}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/concept">
                <xsl:result-document href="{$filename}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/reference">
                <xsl:result-document href="{$filename}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/topic">
                <xsl:result-document href="{$filename}" method="xml">
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA concept//EN" "concept.dtd"&gt;</xsl:text>
                    <xsl:apply-templates/>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/note">
                <xsl:result-document href="{$filename}" method="xml"  >
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
                    <concept class="- topic/topic concept/concept " id="{$filename}" xml:lang="EN-US">
                        <title class="- topic/title "><xsl:value-of select="substring-before($filename , '.xml')"/></title>
                        <conbody class="- topic/body  concept/conbody ">
                            <xsl:apply-templates  />
                        </conbody>
                    </concept>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/table">
                <xsl:result-document href="{$filename}" method="xml" >
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
                    <concept class="- topic/topic concept/concept " id="{$filename}" xml:lang="EN-US">
                        <title class="- topic/title "><xsl:value-of select="substring-before($filename , '.xml')"/></title>
                        <conbody class="- topic/body  concept/conbody ">
                            <xsl:apply-templates />
                        </conbody>
                    </concept>
                </xsl:result-document>
            </xsl:when>
            <xsl:when test="/techinfomap">
                <xsl:variable name="bm" select="substring-before($filename , '.xml')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.ditamap' )"/>
                <xsl:result-document href="{$bookmap}" method="xml" >
                    <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd"&gt;</xsl:text>
                    <xsl:apply-templates />
                </xsl:result-document>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>
    
      <!-- This template will remove all the items that match with this template -->
    <xsl:template match="@xsi:noNamespaceSchemaLocation | note/@href | table/@href 
        | @xsi:* | note/@xml:lang | table/@xml:lang" priority="100" />
    
    <xsl:template match="@xml:lang">
        <xsl:attribute name="xml:lang" select="'EN-US'"/>
    </xsl:template>
    
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="techinfomap">
        <bookmap>
            <xsl:apply-templates select="@* | node()"/>
        </bookmap>
    </xsl:template>
    
    <xsl:template match="reference">
        <reference>
            <xsl:apply-templates select="@* | node()"/>
        </reference>
    </xsl:template>
    
    <xsl:template match="chapter">
        <chapter>
            <xsl:apply-templates select="@* | node()"/>
        </chapter>
    </xsl:template>
    
    <xsl:template match="task">
        <task>
            <xsl:apply-templates select="@* | node()"/>
        </task>
    </xsl:template>
    
    <xsl:template match="topic">
        <concept>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/topic concept/concept '"/>
            <xsl:apply-templates select="node()"/>
        </concept>
    </xsl:template>
    
    <xsl:template match="body">
        <conbody>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/body  concept/conbody '"/>
            <xsl:apply-templates select="node()"/>
        </conbody>
    </xsl:template>
    
    <xsl:template match="concept">
        <concept>
            <xsl:apply-templates select="@* | node()"/>
        </concept>
    </xsl:template>
    
    <xsl:template match="bookmap">
        <bookmap>
            <xsl:apply-templates select="@* | node()"/>
        </bookmap>
    </xsl:template>
    
    <xsl:template match="map">
        <map>
            <xsl:apply-templates select="@* | node()"/>
        </map>
    </xsl:template>
    
    <xsl:template match="prodinfo">
        <prodinfo>
            <xsl:apply-templates select="@* | node()"/>
        </prodinfo>
    </xsl:template>
    
    <xsl:template match="part">
        <chapter>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- map/topicref bookmap/chapter '"/>
            <xsl:apply-templates select="node()"/>
        </chapter>
    </xsl:template>
    
    <xsl:template match="chapter">
        <mapref>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'+ map/topicref mapgroup-d/mapref '"/>
            <xsl:apply-templates select="node()"/>
        </mapref>
    </xsl:template>
    
    <xsl:template match="division">
        <xsl:choose>
            <xsl:when test="count( ancestor::division) = 0">
                <!--Remove white space and strange characters -->
                <xsl:variable name="hr1" select="replace( @href, '%27' , '_' )"/>
                <xsl:variable name="hr11" select="replace( $hr1, '%20', '_')"/>
                
                <xsl:variable name="hr111" select="
                    replace(
                    replace(
                    replace($hr11, ' ', '_'),
                    '\+', '_'),
                    '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
                
                
                <xsl:variable name="target_file" select="replace( $hr111 , 'SINGLEQUOTE' , '' )"/>
                <xsl:variable name="target_file_name" select="substring-before(  $target_file, '.xml' )"/>
                <chapter>
                    <xsl:apply-templates select="@*[ not( contains(name() , 'href' ))]"/>
                    <xsl:attribute name="class" select="'- map/topicref bookmap/chapter '"/>
                    <mapref>
                        <xsl:attribute name="class" select="'+ map/topicref mapgroup-d/mapref '"/>
                        <xsl:attribute name="href" select="concat($target_file_name , '.ditamap')"/>
                        <xsl:result-document href="{concat($target_file_name , '.ditamap')}" method="xml" >
                            <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd"&gt;</xsl:text>
                            <map class="- map/map " id="{$target_file_name}" xml:lang="EN-US">
                                <title class="- topic/title "><xsl:value-of select="$target_file_name"/></title>
                                    <topicref>
                                        <xsl:apply-templates select="@*"/>
                                        <xsl:attribute name="class" select="'- map/topicref '"/>
                                        <xsl:attribute name="href" select="$target_file"/>
                                        <xsl:choose>
                                            <xsl:when test="@type eq 'topic'">
                                                <xsl:attribute name="type">concept</xsl:attribute>
                                            </xsl:when>
                                            <xsl:otherwise/>
                                        </xsl:choose>
                                        <xsl:apply-templates select="node()"/>
                                    </topicref>
                                </map>
                            </xsl:result-document>
                    </mapref>
                </chapter>
            </xsl:when>
            <xsl:otherwise>
                <topicref>
                    <xsl:apply-templates select="@*"/>
                    <xsl:attribute name="class" select="'- map/topicref '"/>
                    <xsl:choose>
                        <xsl:when test="@type eq 'topic'">
                            <xsl:attribute name="type">concept</xsl:attribute>
                        </xsl:when>
                        <xsl:otherwise/>
                    </xsl:choose>
                    <xsl:apply-templates select="node()"/>
                </topicref>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="@navtitle" />
    
    <xsl:template match="techinfomap/subtitle" priority="100" /> 
    
    <xsl:template match="subtitle" mode="bookmap-subtitle">
        <booktitlealt class="- topic/ph bookmap/booktitlealt "  >
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/ph bookmap/booktitlealt '"/>
            <xsl:apply-templates select="node()"/>
        </booktitlealt>
    </xsl:template> 
    
    <xsl:template match="subtitle">
        <booktitlealt class="- topic/ph bookmap/booktitlealt "  >
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/ph bookmap/booktitlealt '"/>
            <xsl:apply-templates select="node()"/>
        </booktitlealt>
    </xsl:template>
    
    <xsl:template match="techinfomap/title" >
        <booktitle class="- topic/title bookmap/booktitle ">
            <mainbooktitle>
                    <xsl:apply-templates select="@*"/>
                <xsl:attribute name="class" select="'- topic/ph bookmap/mainbooktitle '"/>
                    <xsl:apply-templates select="node()"/>
            </mainbooktitle>
            <xsl:apply-templates select="following-sibling::subtitle[1]" mode="bookmap-subtitle"/>
        </booktitle>
    </xsl:template>
    
    <xsl:template match="techinfometa" >
        <bookmeta>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- map/topicmeta bookmap/bookmeta '"/>
            <xsl:apply-templates select="node()"/>
            <bookid class="- topic/data bookmap/bookid "  >
                <xsl:apply-templates select="//revised[1]" mode="bookmap-revised"/>
                <xsl:apply-templates select="./serialno" mode="bookmap-serialno"/>
            </bookid>
            <xsl:apply-templates select="./copyright" mode="bookmap-copyright"/>
        </bookmeta>
    </xsl:template>
    
    <xsl:template match="techinfometa/copyright" priority="100" />
    
    <xsl:template match="copyright">
        <bookrights>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/bookrights '"/>
            <xsl:apply-templates select="node()"/>
        </bookrights>
    </xsl:template>
    
    <xsl:template match="copyright" mode="bookmap-copyright">
        <bookrights>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/bookrights '"/>
            <xsl:apply-templates select="node()"/>
        </bookrights>
    </xsl:template>
    
    <xsl:template match="revised" priority="100" />
    
    <xsl:template match="revised" mode="bookmap-revised">
        <edition>
            <xsl:attribute name="class" select="'- topic/data bookmap/edition '"/>
            <xsl:value-of select="@modified"/>
        </edition>
    </xsl:template>
    
    <xsl:template match="techinfometa/serialno" priority="100" />
    
    <xsl:template match="serialno">
        <booknumber>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/booknumber '"/>
            <xsl:apply-templates select="node()"/>
        </booknumber>
    </xsl:template>
    
    <xsl:template match="serialno" mode="bookmap-serialno">
        <booknumber>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/booknumber '"/>
            <xsl:apply-templates select="node()"/>
        </booknumber>
    </xsl:template>
    
    <xsl:template match="copyryear">
        <copyrfirst>
            <xsl:apply-templates select="@*[ not( contains( name() , 'year') ) ]"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/copyrfirst '"/>
            <year class="- topic/ph bookmap/year " ><xsl:value-of select="@year"/></year>
        </copyrfirst>
    </xsl:template>
    
    <xsl:template match="copyrholder">
        <bookowner>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data bookmap/bookowner '"/>
            <organization class="- topic/ph bookmap/year " >
                <xsl:apply-templates select="node()"/>
            </organization>
        </bookowner>
    </xsl:template>
    
    <xsl:template match="critdates">
        <critdates>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/critdates '"/>
            <xsl:apply-templates select="node()"/>
        </critdates>
    </xsl:template>
    
    <xsl:template match="created">
        <created>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/critdates '"/>
            <xsl:apply-templates select="node()"/>
        </created>
    </xsl:template>
    
    <xsl:template match="revised">
        <revised>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/revised '"/>
            <xsl:apply-templates select="node()"/>
        </revised>
    </xsl:template>
    
    <xsl:template match="div">
        <div>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/div '"/>
            <xsl:apply-templates select="node()"/>
        </div>
    </xsl:template>
    
    
    <xsl:template match="techinfomap/techinfometa/category" priority="100" />
    
    <xsl:template match="category" >
        <category>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/category '"/>
            <xsl:apply-templates select="node()"/>
        </category>
    </xsl:template>
    
    <xsl:template match="category" mode="bookmap-category">
        <category>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/category '"/>
            <xsl:apply-templates select="node()"/>
        </category>
    </xsl:template>
    
    <xsl:template match="metadata" >
        <metadata>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/metadata '"/>
            <xsl:apply-templates select="preceding-sibling::category" mode="bookmap-category"/>
            <xsl:apply-templates select="following-sibling::category" mode="bookmap-category"/>
            <xsl:apply-templates select="node()"/>
            <xsl:apply-templates select="preceding-sibling::productgraphic" mode="bookmap-productgraphic"/>
            <xsl:apply-templates select="following-sibling::productgraphic" mode="bookmap-productgraphic"/>
        </metadata>
    </xsl:template>
    
    <xsl:template match="othermeta" >
        <category>
            <xsl:attribute name="class" select="'- topic/category '"/>
            <xsl:value-of select="@content"/>
        </category>
        <othermeta>
            <xsl:attribute name="class" select="'- topic/othermeta '"/>
            <xsl:attribute name="name" select="'Legal restrictions'"/>
            <xsl:attribute name="content" select="@name"/>
        </othermeta>
    </xsl:template>
    
    <xsl:template match="techinfomap/techinfometa/productgraphic" priority="100" />
    
    <xsl:template match="productgraphic" >
        <data>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data '"/>
            <xsl:apply-templates select="node()"/>
        </data>
    </xsl:template>
    
    <xsl:template match="productgraphic" mode="bookmap-productgraphic">
        <data>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="class" select="'- topic/data '"/>
            <xsl:if test="self::*/image">
                <xsl:attribute name="name" select="'cover_image'" />
            </xsl:if>
            <xsl:apply-templates select="node()"/>
        </data>
    </xsl:template>
    
    <xsl:template match="toc" >
        <xsl:choose>
            <xsl:when test="ancestor::frontmatter">
                <toc>
                    <xsl:apply-templates select="@*"/>
                    <xsl:attribute name="class" select="'- map/topicref bookmap/toc '"/>
                    <xsl:apply-templates select="node()"/>
                </toc>
            </xsl:when>
            <xsl:otherwise>
                <frontmatter class="- map/topicref bookmap/frontmatter ">
                    <booklists class="- map/topicref bookmap/booklists ">
                        <toc>
                            <xsl:apply-templates select="@*"/>
                            <xsl:attribute name="class" select="'- map/topicref bookmap/toc '"/>
                            <xsl:apply-templates select="node()"/>
                        </toc>
                    </booklists>
                </frontmatter>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="@href">
        <!--Remove white space and strange characters -->
        <xsl:variable name="href0" select="tokenize( . , '/')[last()]"/>
        <xsl:variable name="href00" select="replace( $href0, '%27' , '_' )"/>
        <xsl:variable name="href1" select="replace( $href00, '%20', '_')"/>
        
        <xsl:variable name="href11" select="
            replace(
            replace(
            replace($href1, ' ', '_'),
            '\+', '_'),
            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
        
        <xsl:variable name="path0" select="string(subsequence(tokenize(., '/'), 1, count(tokenize(., '/')) - 1))"/>
        
        <xsl:variable name="href" ><xsl:choose>
            <xsl:when test="$path0"><xsl:value-of select="concat( $path0 , '/' , string( $href11 ))"/></xsl:when>
            <xsl:otherwise><xsl:value-of select="$href11"/></xsl:otherwise>
        </xsl:choose></xsl:variable>
        
        <xsl:variable name="href" ><xsl:choose>
            <xsl:when test="$path0">
                <xsl:choose>
                    <xsl:when test="contains( $path0 , '#' )">
                        <xsl:variable name="path0-0" select="replace( $path0, '%27' , '_' )"/>
                        <xsl:variable name="path00" select="replace( $path0-0, '%20', '_')"/>
                        <!--                <xsl:variable name="path000" select="replace( $path0, '#', 'HASHTAG')"/>-->
                        <xsl:variable name="path000" select="
                            replace(
                            replace(
                            replace($path00, ' ', '_'),
                            '\+', '_'),
                            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
                        <xsl:value-of select="concat( $path000 , '/' , string( $href11 ))"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat( $path0 , '/' , string( $href11 ))"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise><xsl:value-of select="$href11"/></xsl:otherwise>
        </xsl:choose></xsl:variable>
        
        <xsl:choose>
            <xsl:when test="contains( . ,  '.eps')">
                <xsl:variable name="bm" select="substring-before($href , '.eps')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.svg' )"/>
                <xsl:attribute name="href" select="$bookmap"/>
            </xsl:when>
            <xsl:when test="contains( . ,  '.tiff')">
                <xsl:variable name="bm" select="substring-before($href , '.tiff')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.png' )"/>
                <xsl:attribute name="href" select="$bookmap"/>
            </xsl:when>
            <xsl:when test="contains( . ,  '.tif')">
                <xsl:variable name="bm" select="substring-before($href , '.tif')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.png' )"/>
                <xsl:attribute name="href" select="$bookmap"/>
            </xsl:when>
            <xsl:when test=" ancestor::*/@format = ('map' , 'ditamap' )">
                <xsl:variable name="bm" select="substring-before($href , '.xml')"/>
                <xsl:variable name="bookmap" select="concat($bm , '.ditamap' )"/>
                <xsl:attribute name="href" select="$bookmap"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="href" select="$href"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    
    
    <xsl:template match="@id">
        <!--Remove white space and strange characters -->
        <xsl:variable name="href0" select="."/>
        <xsl:variable name="href00" select="replace( $href0, '%27' , '_' )"/>
        <xsl:variable name="href1" select="replace( $href00, '%20', '_')"/>
        
        <xsl:variable name="href11" select="
            replace(
            replace(
            replace($href1, ' ', '_'),
            '\+', '_'),
            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
        
        <xsl:attribute name="id" select="$href11"/>
    </xsl:template>
    
    <xsl:template match="@conref">
        <!--Remove white space and strange characters -->
        <xsl:variable name="href0" select="."/>
        <xsl:variable name="href00" select="replace( $href0, '%27' , '_' )"/>
        <xsl:variable name="href1" select="replace( $href00, '%20', '_')"/>
        
        <xsl:variable name="href11" select="
            replace(
            replace(
            replace($href1, ' ', '_'),
            '\+', '_'),
            '[^\w.\-_#/]|[\(\)\[\]\{\}]', '')"/>
        
        <xsl:attribute name="conref" select="$href11"/>
    </xsl:template>
    
    <xsl:template match="atict:info"/>
    <xsl:template match="atict:user"/>

    <xsl:template match="table[not(child::*)]" >
        <table>
            <xsl:apply-templates select="@*"/>
            <tgroup cols="2">
                <tbody>
                    <row>
                        <entry/>
                    </row>
                </tbody>
            </tgroup>
        </table>
    </xsl:template>
    
<!--    <xsl:template match="table[not(node()) and not(text())]" />-->
        
    
    <xsl:template match="@xml:base">
        <!--Remove white space and strange characters -->
        <xsl:variable name="href0" select="tokenize( . , '/')[last()]"/>
        <xsl:variable name="href0-0" select="replace( $href0, '%27' , '_' )"/>
        <xsl:variable name="href1" select="replace( $href0-0, '%20', '_')"/>
        
        <xsl:variable name="href11" select="
            replace(
            replace(
            replace($href1, ' ', '_'),
            '\+', '_'),
            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
        
        <xsl:variable name="path0" select="string(subsequence(tokenize(., '/'), 1, count(tokenize(., '/')) - 1))"/>
        
        <xsl:variable name="href" ><xsl:choose>
            <xsl:when test="$path0"><xsl:value-of select="concat( $path0 , '/' , string( $href11 ))"/></xsl:when>
            <xsl:otherwise><xsl:value-of select="$href11"/></xsl:otherwise>
        </xsl:choose></xsl:variable>
        
        <xsl:variable name="href" ><xsl:choose>
            <xsl:when test="$path0">
                <xsl:choose>
                    <xsl:when test="contains( $path0 , '#' )">
                        <xsl:variable name="path0-0" select="replace( $path0, '%27' , '_' )"/>
                        <xsl:variable name="path00" select="replace( $path0-0, '%20', '_')"/>
                        <!--                <xsl:variable name="path000" select="replace( $path0, '#', 'HASHTAG')"/>-->
                        
                        <xsl:variable name="path000" select="
                            replace(
                            replace(
                            replace($path00, ' ', '_'),
                            '\+', '_'),
                            '[^\w.\-_]|[\(\)\[\]\{\}]', '')"/>
                        
                        <xsl:value-of select="concat( $path000 , '/' , string( $href11 ))"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat( $path0 , '/' , string( $href11 ))"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise><xsl:value-of select="$href11"/></xsl:otherwise>
        </xsl:choose></xsl:variable>
        <xsl:attribute name="conref"><xsl:value-of select="concat($href , '#' , $href , '/' ,  parent::*/@id)"/></xsl:attribute>
    </xsl:template>
    
    
    
    <!-- Change prereq to mtask element prereqs -->
    <xsl:template match="prereq">
        <prelreqs>
            <xsl:attribute name="class">+ topic/section task/prereq taskreq-d/prelreqs </xsl:attribute>

            <reqconds>
                <xsl:attribute name="class">+ topic/ul task/ul taskreq-d/reqconds </xsl:attribute>
                <reqcond>
                    <xsl:attribute name="class">+ topic/li task/li taskreq-d/reqcond </xsl:attribute>
                    <xsl:apply-templates select="@* | node()"/>
                </reqcond>
            </reqconds>

        </prelreqs>
    </xsl:template>
    <!-- Change postreq to mtask element closereqs -->
    <xsl:template match="postreq">
        <closereqs>
            <xsl:attribute name="class">+ topic/section task/postreq taskreq-d/closereqs </xsl:attribute>

            <reqconds>
                <xsl:attribute name="class">+ topic/ul task/ul taskreq-d/reqconds </xsl:attribute>
                <reqcond>
                    <xsl:attribute name="class">+ topic/li task/li taskreq-d/reqcond </xsl:attribute>
                    <xsl:apply-templates select="@* | node()"/>
                </reqcond>
            </reqconds>

        </closereqs>
    </xsl:template>

</xsl:stylesheet>
